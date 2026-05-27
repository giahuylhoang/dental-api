"""Full Market Mall denture clinic seed: clinic + hours + providers +
availability + FAQs + rag_docs (with Gemini embeddings).

Idempotent. Safe to re-run — FAQs and rag_docs are replaced (cleared and
re-inserted); clinics / providers / availability / hours use upsert.

Run after `alembic upgrade head` against the target DB.

Env:
  DATABASE_URL         (required) — Postgres URL. For Cloud SQL via local
                       proxy, use a TCP form like postgresql://user:pass@127.0.0.1:5432/db
  GEMINI_API_KEY       (required for RAG embedding) — Google API key with
                       Generative Language API enabled.

Usage:
  cd dental-api
  uv run python scripts/seed_market_mall_full.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import time
from pathlib import Path

from dotenv import load_dotenv

_root = Path(__file__).resolve().parent.parent
for env_file in (_root / ".env.local", _root / ".env"):
    if env_file.exists():
        load_dotenv(env_file)
        break
sys.path.insert(0, str(_root))

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker

from database.models import Clinic, Provider, ProviderAvailability  # noqa: E402
from database.v1_1.models import ClinicOperatingHours  # noqa: E402
from database.ops.rag import ClinicFaq, RagDoc  # noqa: E402
from services.rag.embeddings import embed  # noqa: E402


CLINIC_ID = "market-mall-denture"
CLINIC_NAME = "Market Mall Denture Clinic"

# 0=Mon ... 6=Sun
CLINIC_HOURS = [
    (0, time(9, 0), time(17, 0), False),
    (1, time(9, 0), time(17, 0), False),
    (2, time(9, 0), time(17, 0), False),
    (3, time(9, 0), time(17, 0), False),
    (4, time(9, 0), time(18, 30), False),
    (5, None, None, True),
    (6, None, None, True),
]

# Two denturists with their availability windows.
PROVIDERS = [
    {
        "name": "Soheil",
        "title": "Denturist",
        "specialty": "Denturist",
        "availability": [
            # (weekday, start_h, start_m, end_h, end_m)
            (1, 9, 0, 17, 0),   # Tuesday: full day
            (2, 9, 0, 12, 0),   # Wednesday: half day
            (4, 15, 0, 18, 30), # Friday: afternoon
        ],
    },
    {
        "name": "Nadeem",
        "title": "Denturist",
        "specialty": "Denturist",
        "availability": [
            (0, 9, 0, 17, 0),   # Mon
            (1, 9, 0, 17, 0),   # Tue
            (2, 9, 0, 17, 0),   # Wed
            (3, 9, 0, 17, 0),   # Thu
            (4, 9, 0, 12, 0),   # Fri morning
        ],
    },
]

# Short Q&A surfaced in the system prompt at agent dispatch.
FAQS = [
    ("What insurance do you accept?",
     "We accept the Canadian Dental Care Plan, also known as C D C P. For other plans, please check with your provider.",
     1),
    ("What are your hours?",
     "Monday to Thursday, nine A M to five P M. Friday, nine A M to six thirty P M. Closed Saturday and Sunday.",
     2),
    ("How much do new dentures cost?",
     "New dentures typically start between seventeen hundred and twenty two hundred dollars. The denturist will give you an exact quote during your consultation.",
     3),
    ("Do I need a referral?",
     "No referral is needed. Just give us a call to book.",
     4),
    ("Are Soheil and Nadeem doctors?",
     "They are licensed Denturists, not doctors. Denturists are specialists in dentures.",
     5),
    ("How long is a consultation?",
     "About thirty minutes. The denturist will determine whether you need full, partial, or implant overdentures.",
     6),
    ("Do you take walk-ins?",
     "We see patients by appointment. If you call now, we can find the next opening.",
     7),
    ("Where are you located?",
     "Suite two twenty seven, four nine three five forty Avenue Northwest, in Calgary.",
     8),
    ("How do I pronounce Nadeem?",
     "Nadeem is pronounced Na-deem.",
     9),
]

# Longer prose embedded for semantic retrieval via /rag/answer.
RAG_DOCS = [
    (
        "Clinic team and professional titles",
        "Market Mall Denture Clinic is staffed by two licensed Denturists: Soheil and Nadeem. They are professional denturists — specialists in denture fitting and care — not dentists or medical doctors. When a caller refers to them as 'doctor', gently use the term 'denturist' instead in your next sentence. Nadeem is pronounced Na-deem.",
        "Soheil and Nadeem are licensed Denturists at Market Mall Denture Clinic — denture specialists, not doctors. Nadeem is pronounced Na-deem.",
    ),
    (
        "Clinic hours and weekly practitioner schedule",
        "Clinic hours: Monday through Thursday nine A M to five P M, Friday nine A M to six thirty P M, closed Saturday and Sunday. Soheil works Tuesday full day, Wednesday morning from nine to noon, and Friday afternoon from three to six thirty. Nadeem works Monday through Thursday nine to five, and Friday morning nine to noon. Never offer Soheil on a Monday, Thursday, or Friday morning. Never offer Nadeem on a Friday afternoon.",
        "Clinic is open Monday to Thursday nine to five, Friday nine to six thirty, closed weekends. Soheil is in Tuesday, Wednesday morning, and Friday afternoon. Nadeem is in Monday through Thursday and Friday morning.",
    ),
    (
        "Canadian Dental Care Plan and insurance",
        "Market Mall Denture Clinic accepts the Canadian Dental Care Plan, also known as C D C P. For other insurance providers such as Alberta Blue Cross, Sun Life, or Manulife, the clinic can submit claims but actual coverage depends on the patient's specific policy. When discussing cost on the phone, always lead with C D C P acceptance before quoting any numbers.",
        "We accept the Canadian Dental Care Plan. For other insurers like Blue Cross or Sun Life, we can submit claims but coverage depends on your specific plan.",
    ),
    (
        "Initial consultation process",
        "Initial consultations are thirty minutes long. During the consult, the denturist determines whether the patient needs full dentures, partial dentures, or implant overdentures, based on what teeth remain and the shape of the gums. If a caller asks about specific procedural steps like impressions or fittings, explain that those are handled during treatment and the right first step is a thirty-minute consultation.",
        "Initial consultations are thirty minutes. The denturist will figure out whether you need full, partial, or implant overdentures during the consult.",
    ),
    (
        "Pricing for new dentures",
        "New dentures typically start between seventeen hundred and twenty two hundred dollars. The final cost depends on the specific case — number of teeth, materials chosen, and any specialty work. The denturist provides an exact quote during the consultation. Do not commit to specific prices on the phone — give the typical range and explain the quote comes during the consult.",
        "New dentures usually start between seventeen hundred and twenty two hundred dollars. The exact quote comes during your consultation.",
    ),
    (
        "Triage questions for new bookings",
        "Before booking a new appointment, ask three triage questions: are you a new patient or an existing patient, do you currently have dentures, and were you referred to us by another clinic or a friend. These answers help match the caller to the right denturist and the right appointment type.",
        "Before booking, we usually ask if you're a new or existing patient, whether you currently have dentures, and whether you were referred to us.",
    ),
    (
        "Reline post-op care",
        "A reline reshapes the inside of an existing denture to fit the gums better. Most relines take about an hour and the patient wears them home the same day. Some snugness in the first day or two is normal. Avoid very hot drinks for the first twelve hours. If sore spots last more than seventy-two hours, call the clinic for a quick adjustment.",
        "A reline reshapes your denture to fit your gums better. Takes about an hour, you wear them home. Call us if any sore spots last more than three days.",
    ),
    (
        "Partial versus full dentures",
        "A partial denture replaces some missing teeth and clasps onto the remaining natural teeth. A full denture replaces all teeth on the top or bottom arch. Both can be made from acrylic or a flexible nylon. The denturist recommends a type based on the number of teeth remaining and the shape of the gums.",
        "Partial dentures replace some missing teeth and attach to the remaining ones. Full dentures replace all the teeth on top or bottom. The denturist will recommend the right type.",
    ),
    (
        "Immediate dentures",
        "Immediate dentures are placed on the same day remaining teeth are extracted, so the patient is never without teeth in public. Healing takes about six months and the gums change shape during that period. The denture will need to be relined once everything settles.",
        "Immediate dentures go in the same day your remaining teeth come out. They usually need a reline after about six months once your gums have healed.",
    ),
]


def upsert_clinic(db):
    c = db.get(Clinic, CLINIC_ID)
    if c is None:
        db.add(Clinic(id=CLINIC_ID, name=CLINIC_NAME))
        print(f"  + clinic {CLINIC_ID} created")
    elif c.name != CLINIC_NAME:
        c.name = CLINIC_NAME
        print(f"  ~ clinic {CLINIC_ID} name updated")
    else:
        print(f"  = clinic {CLINIC_ID} already correct")
    db.commit()


def upsert_hours(db):
    db.execute(delete(ClinicOperatingHours).where(ClinicOperatingHours.clinic_id == CLINIC_ID))
    for dow, open_at, close_at, closed in CLINIC_HOURS:
        db.add(ClinicOperatingHours(
            clinic_id=CLINIC_ID, day_of_week=dow,
            open_at=open_at or time(0, 0), close_at=close_at or time(0, 0),
            is_closed=closed,
        ))
    db.commit()
    print(f"  + clinic_operating_hours: {len(CLINIC_HOURS)} rows")


def upsert_providers(db):
    """Upsert by (clinic_id, name). Replace availability for each."""
    for p in PROVIDERS:
        prov = db.scalar(
            select(Provider).where(Provider.clinic_id == CLINIC_ID, Provider.name == p["name"])
        )
        if prov is None:
            prov = Provider(
                clinic_id=CLINIC_ID, name=p["name"], title=p["title"],
                specialty=p["specialty"], is_active=True,
            )
            db.add(prov)
            db.flush()
            print(f"  + provider {p['name']} created (id={prov.id})")
        else:
            prov.title = p["title"]
            prov.specialty = p["specialty"]
            prov.is_active = True
            print(f"  ~ provider {p['name']} updated (id={prov.id})")
        # Replace availability
        db.execute(delete(ProviderAvailability).where(ProviderAvailability.provider_id == prov.id))
        for (wd, sh, sm, eh, em) in p["availability"]:
            db.add(ProviderAvailability(
                clinic_id=CLINIC_ID, provider_id=prov.id,
                weekday=wd, start_hour=sh, start_minute=sm,
                end_hour=eh, end_minute=em,
            ))
        print(f"    availability: {len(p['availability'])} windows")
    db.commit()


def upsert_faqs(db):
    db.execute(delete(ClinicFaq).where(ClinicFaq.clinic_id == CLINIC_ID))
    for q, a, o in FAQS:
        db.add(ClinicFaq(clinic_id=CLINIC_ID, question=q, answer=a, ordering=o))
    db.commit()
    print(f"  + clinic_faqs: {len(FAQS)} rows")


async def upsert_rag_docs(db):
    db.execute(delete(RagDoc).where(RagDoc.clinic_id == CLINIC_ID))
    db.commit()
    for title, content, voice_ready in RAG_DOCS:
        vec = await embed(content)
        db.add(RagDoc(
            clinic_id=CLINIC_ID, doc_title=title, content=content,
            voice_ready=voice_ready, embedding=vec, doc_metadata={},
        ))
    db.commit()
    print(f"  + rag_docs: {len(RAG_DOCS)} rows (with Gemini embeddings)")


async def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("FAIL: DATABASE_URL not set", file=sys.stderr)
        sys.exit(2)
    safe_url = db_url.split("@", 1)[-1] if "@" in db_url else db_url
    print(f"Connecting to ...@{safe_url}")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        print("[1/5] Clinic")
        upsert_clinic(db)
        print("[2/5] Operating hours")
        upsert_hours(db)
        print("[3/5] Providers + availability")
        upsert_providers(db)
        print("[4/5] FAQs")
        upsert_faqs(db)
        print("[5/5] RAG docs (computing Gemini embeddings)")
        await upsert_rag_docs(db)
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
