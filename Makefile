SHELL := /bin/bash
.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Phase 0 / common gates
# ---------------------------------------------------------------------------

V1_GATE := uv run pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q

.PHONY: help
help:
	@echo "Common targets:"
	@echo "  make phase0           Run Phase 0 verification (deps + alembic + v1 gate + frontend build)"
	@echo "  make test-v1          Run only the v1 backwards-compatibility gate"
	@echo "  make test-all         Run every backend test + frontend tests"
	@echo "  make alembic-check    Apply migrations on a throwaway SQLite DB"
	@echo ""
	@echo "Per-track tests (assumes track has produced its files):"
	@echo "  make test-track-1     Auth/RBAC/Audit"
	@echo "  make test-track-2     Clinical / Lab / Treatment plans"
	@echo "  make test-track-3     Scheduling / Billing / Insurance / Comms / CRM"
	@echo "  make test-track-4     Frontend shell + clinical UI"
	@echo "  make test-track-5     Frontend ops UI"
	@echo ""
	@echo "Auto-fix loops (drive a kiro session until tests pass):"
	@echo "  make loop-track-N     Spawn a kiro agent on docs/tracks/track-N.md until its gate is green"

.PHONY: phase0
phase0: alembic-check test-v1 frontend-build
	@echo "[Phase 0] Verified: alembic clean, v1 gate green, frontend builds."

.PHONY: test-v1
test-v1:
	$(V1_GATE)

.PHONY: alembic-check
alembic-check:
	@rm -f _alembic_check.db
	DATABASE_URL=sqlite:///./_alembic_check.db uv run alembic upgrade head
	@rm -f _alembic_check.db

.PHONY: frontend-build
frontend-build:
	@if [ -d frontend ] && [ -f frontend/package.json ]; then \
	  cd frontend && npm install --silent && npm run build; \
	else \
	  echo "[frontend-build] skipped (frontend/ not scaffolded)"; \
	fi

.PHONY: test-all
test-all: test-v1
	@if [ -d tests/track_auth ];     then uv run pytest tests/track_auth -q;     fi
	@if [ -d tests/track_clinical ]; then uv run pytest tests/track_clinical -q; fi
	@if [ -d tests/track_ops ];      then uv run pytest tests/track_ops -q;      fi
	@if [ -d frontend ]; then \
	  cd frontend && \
	  ([ -d tests/track_clinical ] && npm run -s test:track-4 || true) && \
	  ([ -d tests/track_ops ]      && npm run -s test:track-5 || true); \
	fi

# ---------------------------------------------------------------------------
# Per-track test gates
# ---------------------------------------------------------------------------

.PHONY: test-track-1
test-track-1:
	uv run pytest tests/track_auth -q
	$(V1_GATE)

.PHONY: test-track-2
test-track-2:
	uv run pytest tests/track_clinical -q
	$(V1_GATE)

.PHONY: test-track-3
test-track-3:
	uv run pytest tests/track_ops -q
	$(V1_GATE)

.PHONY: test-track-4
test-track-4:
	@for f in \
	  frontend/src/features/patients/PatientList.tsx \
	  frontend/src/features/patients/Patient360.tsx \
	  frontend/src/features/clinical/notes/SoapEditor.tsx \
	  frontend/src/features/clinical/denture-cases/DentureCaseTimeline.tsx \
	  frontend/src/features/lab/LabCaseKanban.tsx \
	  frontend/src/features/treatment-plans/TreatmentPlanEditor.tsx \
	  frontend/tests/track_clinical/patient360.test.tsx \
	  frontend/tests/track_clinical/soap-locking.test.tsx; do \
	    [ -f $$f ] || { echo "Track 4 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s gen:api && npm run -s build && \
	  npm run -s test:track-4 && npm run -s e2e:track-4

.PHONY: test-track-5
test-track-5:
	@for f in \
	  frontend/src/features/scheduling/Calendar.tsx \
	  frontend/src/features/scheduling/NewAppointmentDialog.tsx \
	  frontend/src/features/billing/InvoiceEditor.tsx \
	  frontend/src/features/billing/InvoiceList.tsx \
	  frontend/src/features/communications/CommInbox.tsx \
	  frontend/src/features/crm/LeadKanban.tsx \
	  frontend/src/features/reporting/Dashboard.tsx \
	  frontend/tests/track_ops/invoice-math.test.ts \
	  frontend/tests/track_ops/lead-conversion.test.ts; do \
	    [ -f $$f ] || { echo "Track 5 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:track-5 && npm run -s e2e:track-5

# ---------------------------------------------------------------------------
# Auto-fix loops (kiro-cli)
# ---------------------------------------------------------------------------
#
# kiro-cli (NOT the Electron `kiro` IDE) is the headless CLI agent.
# We drive the auto-fix loop in shell: invoke kiro-cli with the brief once;
# after it returns, re-run the test gate; if it failed, resume and try again.
# Cap retries with KIRO_MAX_ITERATIONS to bound the budget.
#
# Each iteration logs to logs/track-N.log so you can tail the output:
#     tail -f logs/track-1.log
# ---------------------------------------------------------------------------

KIRO_MAX_ITERATIONS ?= 25
KIRO_BIN ?= kiro-cli

# Template:
#   $(1) = track number (1..5)
#
# Each iteration: run gate; if green, done. Else, send brief + failing
# output to kiro-cli as a single self-contained prompt. We deliberately do
# NOT use --resume because running 5 loops from the same dir would step on
# each other's session storage.
define run_loop
	@mkdir -p logs
	@brief="$$(cat docs/tracks/track-$(1).md)"; \
	i=0; \
	while [ $$i -lt $(KIRO_MAX_ITERATIONS) ]; do \
	  i=$$((i+1)); \
	  echo "[track-$(1)] iteration $$i — running gate..." | tee -a logs/track-$(1).log; \
	  if gate=$$($(MAKE) test-track-$(1) 2>&1); then \
	    echo "[track-$(1)] GREEN after $$i iteration(s)."; \
	    exit 0; \
	  fi; \
	  echo "$$gate" >> logs/track-$(1).log; \
	  echo "[track-$(1)] gate red; invoking $(KIRO_BIN)..." | tee -a logs/track-$(1).log; \
	  prompt=$$(printf '%s\n\n---\n\nGate command: `$(MAKE) test-track-$(1)`\nLatest gate failure (last 200 lines):\n```\n%s\n```\n\nImplement / fix according to the brief above so the gate exits 0. You MUST keep `$(MAKE) test-v1` green at every step.' "$$brief" "$$(echo "$$gate" | tail -n 200)"); \
	  $(KIRO_BIN) chat --no-interactive --trust-all-tools "$$prompt" 2>&1 | tee -a logs/track-$(1).log; \
	done; \
	echo "[track-$(1)] iteration budget ($(KIRO_MAX_ITERATIONS)) exhausted; gate still red." | tee -a logs/track-$(1).log; \
	exit 1
endef

.PHONY: loop-track-1 loop-track-2 loop-track-3 loop-track-4 loop-track-5
loop-track-1: ; $(call run_loop,1)
loop-track-2: ; $(call run_loop,2)
loop-track-3: ; $(call run_loop,3)
loop-track-4: ; $(call run_loop,4)
loop-track-5: ; $(call run_loop,5)

# ---------------------------------------------------------------------------
# PMS Frontend Overhaul tracks (Phase 0 backend gap-fill + P1..P5 frontend)
# ---------------------------------------------------------------------------
#
# Mirror of the run_loop macro for pms-track-pN slugged briefs/gates.
#   $(1) = sub-track id (p0, p1, ..., p5)

define run_pms_loop
	@mkdir -p logs
	@brief="$$(cat docs/tracks/pms-track-$(1).md)"; \
	i=0; \
	while [ $$i -lt $(KIRO_MAX_ITERATIONS_PMS) ]; do \
	  i=$$((i+1)); \
	  echo "[pms-track-$(1)] iteration $$i — running gate..." | tee -a logs/pms-track-$(1).log; \
	  if gate=$$($(MAKE) test-pms-$(1) 2>&1); then \
	    echo "[pms-track-$(1)] GREEN after $$i iteration(s)."; \
	    exit 0; \
	  fi; \
	  echo "$$gate" >> logs/pms-track-$(1).log; \
	  echo "[pms-track-$(1)] gate red; invoking $(KIRO_BIN)..." | tee -a logs/pms-track-$(1).log; \
	  prompt=$$(printf '%s\n\n---\n\nGate command: `$(MAKE) test-pms-$(1)`\nLatest gate failure (last 200 lines):\n```\n%s\n```\n\nImplement / fix according to the brief above so the gate exits 0. You MUST keep `$(MAKE) test-v1` green at every step.' "$$brief" "$$(echo "$$gate" | tail -n 200)"); \
	  $(KIRO_BIN) chat --no-interactive --trust-all-tools "$$prompt" 2>&1 | tee -a logs/pms-track-$(1).log; \
	done; \
	echo "[pms-track-$(1)] iteration budget ($(KIRO_MAX_ITERATIONS_PMS)) exhausted; gate still red." | tee -a logs/pms-track-$(1).log; \
	exit 1
endef

KIRO_MAX_ITERATIONS_PMS ?= 30

.PHONY: pms-loop-p0 pms-loop-p1 pms-loop-p2 pms-loop-p3 pms-loop-p4 pms-loop-p5 pms-loop-all
pms-loop-p0: ; $(call run_pms_loop,p0)
pms-loop-p1: ; $(call run_pms_loop,p1)
pms-loop-p2: ; $(call run_pms_loop,p2)
pms-loop-p3: ; $(call run_pms_loop,p3)
pms-loop-p4: ; $(call run_pms_loop,p4)
pms-loop-p5: ; $(call run_pms_loop,p5)

# Sequential chain — Make stops at the first failing dependency.
pms-loop-all: pms-loop-p0 pms-loop-p1 pms-loop-p2 pms-loop-p3 pms-loop-p4 pms-loop-p5

# --- Test gates ------------------------------------------------------------

.PHONY: test-pms-p0
test-pms-p0:
	uv run pytest tests/track_pms_p0 -q
	$(V1_GATE)
	cd frontend && npm run -s gen:api && npm run -s build

.PHONY: test-pms-p1
test-pms-p1:
	@for f in \
	  frontend/src/components/Drawer.tsx \
	  frontend/src/components/forms/FormField.tsx \
	  frontend/src/features/patients/LifecyclePanel.tsx \
	  frontend/src/features/patients/MedicalForm.tsx \
	  frontend/src/features/patients/InsuranceList.tsx \
	  frontend/src/features/patients/InsuranceDrawer.tsx \
	  frontend/src/features/patients/DocumentUploader.tsx \
	  frontend/src/features/patients/DocumentList.tsx \
	  frontend/src/features/patients/NotesPanel.tsx \
	  frontend/src/features/patients/ToothChart.tsx \
	  frontend/tests/track_pms_p1; do \
	    [ -e $$f ] || { echo "P1 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-p1 && npm run -s e2e:pms-p1
	$(V1_GATE)

.PHONY: test-pms-p2
test-pms-p2:
	@for f in \
	  frontend/src/features/scheduling/AppointmentDrawer.tsx \
	  frontend/src/features/scheduling/DateTimePicker.tsx \
	  frontend/src/features/scheduling/appt-status.ts \
	  frontend/tests/track_pms_p2; do \
	    [ -e $$f ] || { echo "P2 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-p2 && npm run -s e2e:pms-p2
	$(V1_GATE)

.PHONY: test-pms-p3
test-pms-p3:
	@for f in \
	  frontend/src/features/lab/LabCaseDrawer.tsx \
	  frontend/src/features/lab/DentureCaseDrawer.tsx \
	  frontend/src/features/lab/ImplantForm.tsx \
	  frontend/src/features/lab/MaterialConsumptionForm.tsx \
	  frontend/tests/track_pms_p3; do \
	    [ -e $$f ] || { echo "P3 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-p3 && npm run -s e2e:pms-p3
	$(V1_GATE)

.PHONY: test-pms-p4
test-pms-p4:
	@for f in \
	  frontend/src/features/treatment-plans/TreatmentPlansPage.tsx \
	  frontend/tests/track_pms_p4; do \
	    [ -e $$f ] || { echo "P4 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-p4 && npm run -s e2e:pms-p4
	$(V1_GATE)

.PHONY: test-pms-p5
test-pms-p5:
	@for f in \
	  frontend/src/features/billing/InvoiceDrawer.tsx \
	  frontend/src/features/billing/ClaimDrawer.tsx \
	  frontend/src/features/billing/SubmitClaimForm.tsx \
	  frontend/src/features/billing/AdjudicateForm.tsx \
	  frontend/tests/track_pms_p5; do \
	    [ -e $$f ] || { echo "P5 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-p5 && npm run -s e2e:pms-p5
	$(V1_GATE)

# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

.PHONY: dev
dev:
	./run_local.sh

.PHONY: clean
clean:
	rm -rf .pytest_cache _alembic_check.db
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
