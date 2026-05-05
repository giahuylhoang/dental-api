# The Website — Site Map

## How to Run

```
cd frontend/design_system/rockyridgeai-dental.com
python3 -m http.server 5180
open http://127.0.0.1:5180/ui_kits/website/index.html
```

## Auth

Any password of 6 or more characters logs you in as the first demo user (`data/users.js`). No account creation required.

---

## Pages

| File | Purpose | Sidebar Key | Data Files | JSX Components |
|------|---------|-------------|------------|----------------|
| `index.html` | Marketing landing page | — (no sidebar) | — | Nav, Hero, Pillars, Philosophy, CTA |
| `login.html` | Dark-theme login portal | — (no sidebar) | users | Hero, LoginCard |
| `dashboard.html` | Primary PMS dashboard — KPIs, upcoming appointments, patient roster, lab pipeline | Dashboard | patients, appointments, invoices | Sidebar, TopBar, KpiTile, AppointmentCard, PatientCard, LabPipeline, ToothChartTile |
| `patients.html` | Patient roster — searchable, filterable table with drawer detail | Patients | patients, appointments | Sidebar, TopBar, KpiTile, DataTable, Avatar, Breadcrumb, CalendarGrid, ChartCard, Drawer, EmptyState, FilterChips, FormField, IconButton, KanbanBoard, MoneyCell, MonoText, SearchInput, StatusPill, Tabs, ToothChartTile |
| `patient-detail.html` | Single patient chart — demographics, tooth chart, appointment history, invoices | Patients | patients, appointments, invoices | Sidebar, TopBar, ToothChartTile, EmptyState |
| `schedule.html` | Daily / weekly appointment calendar | Schedule | appointments | Sidebar, TopBar |
| `appointment-detail.html` | Single appointment record — provider, procedure, notes | Schedule | appointments | Sidebar, TopBar, EmptyState |
| `treatment.html` | Treatment plan list — active and completed plans per patient | Treatment | patients | Sidebar, TopBar, ToothChartTile |
| `lab.html` | Lab pipeline — Kanban board of active lab cases | The Lab | — | Sidebar, TopBar, KpiTile, LabPipeline, StatusPill |
| `lab-case-detail.html` | Single lab case — case type, status, turnaround, notes | The Lab | — | Sidebar, TopBar, EmptyState |
| `denture-case-detail.html` | Single denture case — impressions, try-in dates, delivery | The Lab | — | Sidebar, TopBar, EmptyState |
| `billing.html` | Billing overview — outstanding invoices, claims, revenue KPIs | Billing | — | Sidebar, TopBar, KpiTile, StatusPill |
| `invoice-detail.html` | Single invoice — line items, OHIP codes, payment status | Billing | invoices | Sidebar, TopBar, EmptyState |
| `reports.html` | Practice analytics — revenue, appointment volume, provider utilisation | Reports | invoices, appointments | Sidebar, TopBar, KpiTile |
| `crm.html` | CRM — lead pipeline, referral sources, conversion funnel | CRM | — | Sidebar, TopBar, KpiTile, StatusPill |
| `lead-detail.html` | Single lead record — contact info, source, follow-up history | CRM | — | Sidebar, TopBar, EmptyState |
| `communications.html` | Communications hub — recall messages, appointment reminders, threads | Communications | — | Sidebar, TopBar, KpiTile |
| `plans.html` | Subscription and feature plans for the clinic account | Plans | — | Sidebar, TopBar, EmptyState |
| `settings.html` | Clinic settings — providers, operatories, billing codes, integrations | Settings | — | Sidebar, TopBar |

## AI Receptionist Admin Prototype

The Receptionist is the AI voice agent that handles calls when the front desk can't. The pages below are a parallel light-theme prototype scoped to the receptionist admin — they coexist with the PMS pages above, share the same tokens, but use a separate `AdminSidebar`.

| File | Purpose | Sidebar Key |
|------|---------|-------------|
| `_prototype/admin-shell.html`         | Shell preview — sidebar + topbar + main slot              | dashboard |
| `_prototype/admin-dashboard.html`     | The Receptionist overview — ROI tiles, trend, quick links | dashboard |
| `_prototype/admin-calls.html`         | The Call Log — filtered list with audio previews          | calls |
| `_prototype/admin-call-detail.html`   | Single call — transcript, audio, engineer view           | calls |
| `_prototype/admin-patients.html`      | The Roster — CRM rollup with drill-in drawer              | patients |
| `_prototype/admin-schedule.html`      | The Schedule — read-only day view, AI vs. front-desk      | schedule |
| `_prototype/admin-routing.html`       | Routing — hours, holidays, transfer rules, simulator     | routing |
| `_prototype/admin-greeting.html`      | Greeting — editable agent greeting + engineer approval    | greeting |

### Components (admin-only)

| File | Purpose |
|------|---------|
| `_prototype/AdminSidebar.jsx` | Navy sidebar scoped to the receptionist admin |

### Data

- `data/admin_mock.js` — `window.ADMIN_MOCK` with clinic identity, routing, greeting, KPIs, calls, transcripts, patients, appointments. Single source for all admin pages.

---

## Data Files (`data/*.js`)

Each file exposes a `window.UPPER_SNAKE` global consumed by the pages above.

| File | Global | Used by |
|------|--------|---------|
| `patients.js` | `PATIENTS` | dashboard, patients, patient-detail, treatment |
| `appointments.js` | `APPOINTMENTS` | dashboard, patients, patient-detail, schedule, appointment-detail, reports |
| `invoices.js` | `INVOICES` | dashboard, patient-detail, invoice-detail, reports |
| `users.js` | `USERS` | login |
| `clinics.js` | `CLINICS` | data/index.js manifest |
| `providers.js` | `PROVIDERS` | data/index.js manifest |
| `services.js` | `SERVICES` | data/index.js manifest |
| `treatment_plans.js` | `TREATMENT_PLANS` | data/index.js manifest |
| `tooth_chart.js` | `TOOTH_CHART` | data/index.js manifest |
| `denture_cases.js` | `DENTURE_CASES` | data/index.js manifest |
| `lab_cases.js` | `LAB_CASES` | data/index.js manifest |
| `claims.js` | `CLAIMS` | data/index.js manifest |
| `recalls.js` | `RECALLS` | data/index.js manifest |
| `waitlist.js` | `WAITLIST` | data/index.js manifest |
| `threads.js` | `THREADS` | data/index.js manifest |
| `leads.js` | `LEADS` | data/index.js manifest |
| `audit_log.js` | `AUDIT_LOG` | data/index.js manifest |
| `index.js` | `RRD` | data/index.js (self) |
