"""Seed Market Mall denture clinic FAQs and rag_docs for the local demo.

Run after alembic upgrade has created the tables. Idempotent — checks for
existing rows before inserting. Also seeds the clinic itself if missing
(reuses scripts.init_database.seed_market_mall_denture).
"""
import asyncio
import os
import sys

# Make sure .env.local is loaded so GEMINI_API_KEY and DATABASE_URL are visible.
from pathlib import Path
from dotenv import load_dotenv
_root = Path(__file__).resolve().parent.parent
for env_file in (_root / ".env.local", _root / ".env"):
    if env_file.exists():
        load_dotenv(env_file)
        break

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Project root on sys.path
sys.path.insert(0, str(_root))

from database.ops.rag import ClinicFaq, RagDoc  # noqa: E402
from services.rag.embeddings import embed  # noqa: E402


CLINIC_ID = "market-mall-denture"

FAQS = [
    ("What are your hours?", "Monday to Friday, nine A M to five P M. We're closed weekends.", 1),
    ("Where are you located?", "3625 Shaganappi Trail Northwest in Calgary. There's free underground parking on level P 2.", 2),
    ("Do you accept Alberta Blue Cross?", "Yes, we accept Alberta Blue Cross. For specific coverage details, please check with your provider.", 3),
    ("Do you take walk-ins?", "We see patients by appointment. If you call now, I can find the next opening.", 4),
    ("How much does a reline cost?", "A standard reline ranges from two fifty to three fifty dollars depending on the work involved. Insurance often covers part of it.", 5),
]

RAG_DOCS = [
    (
        "Reline post-op care",
        "A reline reshapes the inside of your existing denture so it fits your gums better. Most relines take about an hour. After a reline, your denture may feel snug for a day or two as you adjust. Avoid very hot drinks for the first twelve hours. If you notice any sore spots after seventy-two hours, call us and we'll schedule a quick adjustment.",
        "A reline reshapes the inside of your denture so it fits your gums better. Most relines take about an hour and you can wear them home the same day. Some snugness in the first day or two is normal. Call us if any sore spots last more than three days.",
    ),
    (
        "Partial vs full dentures",
        "A partial denture replaces some missing teeth and clasps onto the teeth you still have. A full denture replaces all teeth on the top or bottom. Both can be made from acrylic or a flexible nylon. The dentist will recommend a type based on the number of teeth remaining and the shape of your gums.",
        "Partial dentures replace some of your missing teeth and attach to the remaining ones. Full dentures replace all of the teeth on the top or bottom. The denturist will recommend the right type for your situation.",
    ),
    (
        "Immediate dentures",
        "Immediate dentures are placed on the same day your remaining teeth are extracted, so you're never without teeth in public. Healing takes about six months. During that time, the gums change shape and the denture will need to be relined once everything settles.",
        "Immediate dentures go in the same day your remaining teeth come out, so you don't go without teeth. They usually need a reline after about six months once your gums have healed.",
    ),
]


def _ensure_clinic(db):
    """Create the bare clinic row so the FAQ/RAG FK is satisfied.

    We don't call scripts.init_database.seed_market_mall_denture here because
    it seeds providers + busy blocks against a schema with extra columns
    (weekdays, etc.) that aren't present on this branch yet. RAG only needs
    the clinic row itself.
    """
    from database.models import Clinic
    if db.query(Clinic).filter(Clinic.id == CLINIC_ID).first() is None:
        db.add(Clinic(id=CLINIC_ID, name="Market Mall Denture Clinic"))
        db.commit()
        print(f"Seeded bare clinic {CLINIC_ID}.")
    else:
        print(f"Base clinic {CLINIC_ID} already present.")


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:dev@localhost:5433/dental")
    print(f"Connecting to {db_url}")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        _ensure_clinic(db)

        existing_faqs = db.query(ClinicFaq).filter(ClinicFaq.clinic_id == CLINIC_ID).count()
        if existing_faqs == 0:
            for q, a, o in FAQS:
                db.add(ClinicFaq(clinic_id=CLINIC_ID, question=q, answer=a, ordering=o))
            db.commit()
            print(f"Seeded {len(FAQS)} FAQs.")
        else:
            print(f"FAQs already present ({existing_faqs}). Skipping.")

        existing_docs = db.query(RagDoc).filter(RagDoc.clinic_id == CLINIC_ID).count()
        if existing_docs == 0:
            for title, content, voice_ready in RAG_DOCS:
                vec = await embed(content)
                db.add(RagDoc(
                    clinic_id=CLINIC_ID, doc_title=title, content=content,
                    voice_ready=voice_ready, embedding=vec, doc_metadata={},
                ))
            db.commit()
            print(f"Seeded {len(RAG_DOCS)} rag_docs with embeddings.")
        else:
            print(f"rag_docs already present ({existing_docs}). Skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
