"""Shared serialization helpers used by multiple portal endpoints.

Avoid copy-pasting whitelist/projection logic across api/portal/calls.py,
api/portal/patients.py, etc. — if the FE LeadStatus union drifts, fix in
one place.
"""

from __future__ import annotations

from typing import Literal


# Patient.lead_status_crm column carries CRM-side values that don't all align
# with the frontend's LeadStatus union. Whitelist the ones that do; alias
# 'won' to 'completed' and 'archived' to 'lost'; default unknown to 'new'.
LEAD_STATUS_TO_FE = {
    "new": "new", "contacted": "contacted", "booked": "booked",
    "completed": "completed", "lost": "lost",
    "won": "completed", "archived": "lost",
}


# Values the FE may send on PATCH/POST. Pydantic Literal[...] type enforces
# this at the request boundary so the column never holds garbage that the
# read path then silently coerces back to "new".
LeadStatusInput = Literal[
    "new", "contacted", "booked", "completed", "lost",
    # Legacy aliases — accepted on write, normalized to canonical via the map.
    "won", "archived",
]
