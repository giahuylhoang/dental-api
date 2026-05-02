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
	  $(KIRO_BIN) chat --no-interactive --trust-all-tools --model $(KIRO_PMS_MODEL) "$$prompt" 2>&1 | tee -a logs/pms-track-$(1).log; \
	done; \
	echo "[pms-track-$(1)] iteration budget ($(KIRO_MAX_ITERATIONS_PMS)) exhausted; gate still red." | tee -a logs/pms-track-$(1).log; \
	exit 1
endef

KIRO_MAX_ITERATIONS_PMS ?= 20
KIRO_PMS_MODEL ?= claude-sonnet-4.6

.PHONY: pms-loop-p0 pms-loop-p1 pms-loop-p2 pms-loop-p3 pms-loop-p4 pms-loop-p5 pms-loop-all
pms-loop-p0: ; $(call run_pms_loop,p0)
pms-loop-p1: ; $(call run_pms_loop,p1)
pms-loop-p2: ; $(call run_pms_loop,p2)
pms-loop-p3: ; $(call run_pms_loop,p3)
pms-loop-p4: ; $(call run_pms_loop,p4)
pms-loop-p5: ; $(call run_pms_loop,p5)

# Sequential chain — Make stops at the first failing dependency.
pms-loop-all: pms-loop-p0 pms-loop-p1 pms-loop-p2 pms-loop-p3 pms-loop-p4 pms-loop-p5

# ---------------------------------------------------------------------------
# PMS Modules M0..M6 (interactive overhaul, OSS-adopting)
# ---------------------------------------------------------------------------

.PHONY: pms-mod-m0 pms-mod-m1 pms-mod-m2 pms-mod-m3 pms-mod-m4 pms-mod-m5 pms-mod-m6 pms-mod-all
pms-mod-m0: ; $(call run_pms_loop,m0)
pms-mod-m1: ; $(call run_pms_loop,m1)
pms-mod-m2: ; $(call run_pms_loop,m2)
pms-mod-m3: ; $(call run_pms_loop,m3)
pms-mod-m4: ; $(call run_pms_loop,m4)
pms-mod-m5: ; $(call run_pms_loop,m5)
pms-mod-m6: ; $(call run_pms_loop,m6)
pms-mod-all: pms-mod-m0 pms-mod-m1 pms-mod-m2 pms-mod-m3 pms-mod-m4 pms-mod-m5 pms-mod-m6

.PHONY: test-pms-m0
test-pms-m0:
	@for f in tests/track_pms_m0/__init__.py tests/track_pms_m0/test_m0_endpoints.py ; do \
	  [ -e $$f ] || { echo "M0 test missing: $$f"; exit 1; }; \
	done
	uv run pytest tests/track_pms_m0 -q
	$(V1_GATE)
	cd frontend && npm run -s gen:api && npm run -s build

.PHONY: test-pms-m1
test-pms-m1:
	@for f in \
	  frontend/tests/track_pms_m1/calendar-renders-fullcalendar.test.tsx \
	  frontend/tests/track_pms_m1/select-opens-dialog.test.tsx \
	  frontend/src/features/scheduling/Scheduler.tsx \
	  frontend/src/features/patients/QuickBookPopover.tsx ; do \
	  [ -e $$f ] || { echo "M1 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-m1 && npm run -s e2e:pms-m1
	$(V1_GATE)

.PHONY: test-pms-m2
test-pms-m2:
	@for f in \
	  frontend/tests/track_pms_m2/dropzone-renders.test.tsx \
	  frontend/src/features/patients/DocumentUploader.tsx ; do \
	  [ -e $$f ] || { echo "M2 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-m2 && npm run -s e2e:pms-m2
	$(V1_GATE)

.PHONY: test-pms-m3
test-pms-m3:
	@for f in \
	  frontend/tests/track_pms_m3/editor-shows-tooth-chart.test.tsx \
	  frontend/src/features/treatment-plans/TreatmentPlanEditor.tsx ; do \
	  [ -e $$f ] || { echo "M3 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-m3 && npm run -s e2e:pms-m3
	$(V1_GATE)

.PHONY: test-pms-m4
test-pms-m4:
	@for f in \
	  frontend/tests/track_pms_m4/lead-create-dialog.test.tsx \
	  frontend/src/features/crm/LeadCreateDialog.tsx \
	  frontend/src/features/crm/LeadDrawer.tsx ; do \
	  [ -e $$f ] || { echo "M4 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-m4 && npm run -s e2e:pms-m4
	$(V1_GATE)

.PHONY: test-pms-m5
test-pms-m5:
	@for f in \
	  frontend/tests/track_pms_m5/command-palette-opens-on-cmdk.test.tsx \
	  frontend/src/features/search/CommandPalette.tsx ; do \
	  [ -e $$f ] || { echo "M5 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-m5 && npm run -s e2e:pms-m5
	$(V1_GATE)

.PHONY: test-pms-m6
test-pms-m6:
	@for f in \
	  frontend/tests/track_pms_m6/compose-channel-toggle.test.tsx \
	  frontend/src/features/communications/CommInbox.tsx ; do \
	  [ -e $$f ] || { echo "M6 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-m6 && npm run -s e2e:pms-m6
	$(V1_GATE)

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
# PMS Phase 3 — Feature data fill (F0..F6)
# Goal: every page shows believable data on first paint; Settings real;
# Communications threaded; schema gaps closed; OSS adoption continued.
# ---------------------------------------------------------------------------

.PHONY: pms-fill-f0 pms-fill-f1 pms-fill-f2 pms-fill-f3 pms-fill-f4 pms-fill-f5 pms-fill-f6 pms-fill-all
pms-fill-f0: ; $(call run_pms_loop,f0)
pms-fill-f1: ; $(call run_pms_loop,f1)
pms-fill-f2: ; $(call run_pms_loop,f2)
pms-fill-f3: ; $(call run_pms_loop,f3)
pms-fill-f4: ; $(call run_pms_loop,f4)
pms-fill-f5: ; $(call run_pms_loop,f5)
pms-fill-f6: ; $(call run_pms_loop,f6)
pms-fill-all: pms-fill-f0 pms-fill-f1 pms-fill-f2 pms-fill-f3 pms-fill-f4 pms-fill-f5 pms-fill-f6

.PHONY: test-pms-f0
test-pms-f0:
	@for f in \
	  tests/track_pms_f0/__init__.py \
	  tests/track_pms_f0/test_f0_endpoints.py \
	  scripts/seed_demo_clinic.py \
	  api/v2/settings/router.py ; do \
	  [ -e $$f ] || { echo "F0 deliverable missing: $$f"; exit 1; }; \
	done
	uv run pytest tests/track_pms_f0 -q
	$(V1_GATE)
	cd frontend && npm run -s gen:api && npm run -s build

.PHONY: test-pms-f1
test-pms-f1:
	@for f in \
	  frontend/tests/track_pms_f1/thread-list-renders.test.tsx \
	  frontend/tests/track_pms_f1/compose-patient-autocomplete.test.tsx \
	  frontend/tests/track_pms_f1/reply-prefills-channel-and-to.test.tsx \
	  frontend/src/features/communications/ThreadList.tsx \
	  frontend/src/features/communications/ThreadDetail.tsx \
	  frontend/src/features/communications/ComposeDialog.tsx ; do \
	  [ -e $$f ] || { echo "F1 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-f1
	$(V1_GATE)

.PHONY: test-pms-f2
test-pms-f2:
	@for f in \
	  frontend/tests/track_pms_f2/invoice-list-renders-seeded.test.tsx \
	  frontend/tests/track_pms_f2/invoice-pdf-renders.test.tsx \
	  frontend/src/features/billing/InvoicePdf.tsx ; do \
	  [ -e $$f ] || { echo "F2 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-f2
	$(V1_GATE)

.PHONY: test-pms-f3
test-pms-f3:
	@for f in \
	  frontend/tests/track_pms_f3/case-number-visible-on-card.test.tsx \
	  frontend/tests/track_pms_f3/drawer-shows-linked-plan-link.test.tsx ; do \
	  [ -e $$f ] || { echo "F3 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-f3
	$(V1_GATE)

.PHONY: test-pms-f4
test-pms-f4:
	@for f in \
	  frontend/tests/track_pms_f4/plan-list-shows-status-pills.test.tsx \
	  frontend/tests/track_pms_f4/endpoint-consistency.test.tsx ; do \
	  [ -e $$f ] || { echo "F4 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-f4
	$(V1_GATE)

.PHONY: test-pms-f5
test-pms-f5:
	@for f in \
	  frontend/tests/track_pms_f5/kanban-shows-skeletons-while-loading.test.tsx \
	  frontend/tests/track_pms_f5/drag-fires-correct-status-endpoint.test.tsx ; do \
	  [ -e $$f ] || { echo "F5 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-f5
	$(V1_GATE)

.PHONY: test-pms-f6
test-pms-f6:
	@for f in \
	  frontend/tests/track_pms_f6/settings-loads-clinic-config.test.tsx \
	  frontend/tests/track_pms_f6/save-clinic-info-puts-correct-body.test.tsx \
	  frontend/src/features/settings/SettingsPage.tsx ; do \
	  [ -e $$f ] || { echo "F6 deliverable missing: $$f"; exit 1; }; \
	done
	cd frontend && npm run -s lint && npm run -s build && \
	  npm run -s test:pms-f6
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
