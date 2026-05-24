"""Seed practice_types, clinic_routing, and clinic overrides from the
dental-agent YAML tree.

Idempotent: re-running with the same YAMLs produces the same end state.
The seeder only creates clinic_ai_voice / clinic_ai_disclosure rows when
the clinic's product.yaml actually overrides those fields - so a clinic
that uses the base/<practice>.yaml defaults gets ZERO override rows.

Usage:
    uv run python scripts/seed_clinic_config_from_yaml.py \\
        --yaml-dir ../dental-agent/packages/shared/config/clinics \\
        [--clinic-id market-mall-denture] \\
        [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import (
    Clinic, ClinicAiDisclosure, ClinicAiVoice, ClinicClosure,
    ClinicRouting, PracticeType, Service,
)

logger = logging.getLogger("seed_clinic_config")


# ----- YAML loader (mirrors packages.shared.config.clinic_config) -----

def _deep_merge(parent: dict, child: dict) -> dict:
    out = dict(parent)
    for k, v in (child or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_with_extends(path: Path, _seen: Optional[set] = None) -> dict:
    if _seen is None:
        _seen = set()
    real = path.resolve()
    if real in _seen:
        raise ValueError(f"extends cycle at {path}")
    _seen = _seen | {real}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    extends = data.pop("extends", None)
    if extends:
        parent_path = (path.parent / extends).resolve()
        parent_data = _load_with_extends(parent_path, _seen)
        return _deep_merge(parent_data, data)
    return data


def _load_clinic(clinic_dir: Path) -> dict:
    """Load product.yaml then merge ops.yaml on top (matches the agent's loader)."""
    product = _load_with_extends(clinic_dir / "product.yaml")
    ops_file = clinic_dir / "ops.yaml"
    if ops_file.exists():
        product = _deep_merge(product, _load_with_extends(ops_file))
    return product


def _load_base_for(clinic_dir: Path) -> dict:
    """Load ONLY the parent (base) YAML referenced by product.yaml's `extends`.

    Returns {} if product.yaml has no `extends`. Used to derive practice_type
    defaults independently of the per-clinic overrides.
    """
    product_path = clinic_dir / "product.yaml"
    raw = yaml.safe_load(product_path.read_text(encoding="utf-8")) or {}
    extends = raw.get("extends")
    if not extends:
        return {}
    parent_path = (product_path.parent / extends).resolve()
    return _load_with_extends(parent_path)


# ----- Seeder -----

def _upsert_practice_type(db: Session, base_data: dict, clinic_data: dict) -> str:
    """Upsert the practice_type row from the BASE YAML (not the merged product).

    Falls back to clinic_data when base is empty (a clinic with no `extends`).
    """
    source = base_data if base_data else clinic_data
    clinic_block = source.get("clinic", {}) or {}
    # practice_type id is always taken from the merged clinic data (it's the
    # canonical identifier for the clinic's practice class).
    pt_id = (clinic_data.get("clinic", {}) or {}).get("practice_type") or clinic_block.get("practice_type")
    if not pt_id:
        raise ValueError("Clinic YAML missing clinic.practice_type")
    pt = db.query(PracticeType).filter_by(id=pt_id).one_or_none()
    if pt is None:
        pt = PracticeType(id=pt_id, assistant_name="", ai_disclosure_phrase="",
                          greeting_message="", pricing_preface="",
                          treatment_steps_guardrail="")
        db.add(pt)
    pt.assistant_name = clinic_block.get("assistant_name") or pt.assistant_name or "Emma"
    pt.ai_disclosure_required = bool(clinic_block.get("ai_disclosure_required", True))
    pt.ai_disclosure_phrase = str(clinic_block.get("ai_disclosure_phrase") or pt.ai_disclosure_phrase)
    pt.greeting_message = str(clinic_block.get("greeting_message") or pt.greeting_message)
    pt.pricing_preface = str(clinic_block.get("pricing_preface") or pt.pricing_preface)
    pt.pricing_dentures_range = clinic_block.get("pricing_dentures_range")
    pt.treatment_steps_guardrail = str(clinic_block.get("treatment_steps_guardrail") or pt.treatment_steps_guardrail)
    pt.triage_questions = list(clinic_block.get("triage_questions") or [])
    pt.default_feature_flags = dict(clinic_block.get("feature_flags") or {})
    pt.updated_at = datetime.utcnow()
    return pt_id


def _upsert_clinic_columns(db: Session, clinic_id: str, clinic_data: dict, practice_type_id: str) -> None:
    clinic = db.query(Clinic).filter_by(id=clinic_id).one_or_none()
    if clinic is None:
        raise ValueError(
            f"Clinic row {clinic_id} doesn't exist in DB; create it first via the existing seeder"
        )
    clinic_block = clinic_data.get("clinic", {})
    clinic.practice_type_id = practice_type_id
    clinic.knowledge_base_path = (
        clinic_data.get("knowledge_base_path") or clinic_block.get("knowledge_base_path")
    )
    # general_consultation_service_id is FK-constrained — only set it if the
    # referenced service row exists, otherwise leave the column untouched.
    gcs_id = clinic_data.get("general_consultation_service_id")
    if gcs_id is not None:
        exists = db.query(Service.id).filter_by(id=gcs_id).one_or_none()
        if exists is not None:
            clinic.general_consultation_service_id = gcs_id
        else:
            logger.warning(
                "Skipping general_consultation_service_id=%s for clinic %s "
                "(service row missing; seed services first)", gcs_id, clinic_id,
            )
    # feature_flags_overrides: only fields where the merged product.yaml differs
    # from the practice_type default.
    product_flags: Dict[str, Any] = clinic_block.get("feature_flags") or {}
    pt = db.query(PracticeType).filter_by(id=practice_type_id).one()
    default_flags = pt.default_feature_flags or {}
    overrides = {k: v for k, v in product_flags.items() if default_flags.get(k) != v}
    clinic.feature_flags_overrides = overrides
    if clinic_block.get("address") and not clinic.address:
        clinic.address = clinic_block["address"]
    if clinic_block.get("front_desk_phone") and not clinic.contact_phone:
        clinic.contact_phone = clinic_block["front_desk_phone"]


def _upsert_routing(db: Session, clinic_id: str, routing_block: dict) -> None:
    cr = db.query(ClinicRouting).filter_by(clinic_id=clinic_id).one_or_none()
    if cr is None:
        cr = ClinicRouting(clinic_id=clinic_id)
        db.add(cr)
    cr.ring_timeout_seconds = int(routing_block.get("ring_timeout_seconds", 20))
    cr.ai_after_hours = bool(routing_block.get("ai_after_hours", True))
    cr.ai_in_hours_overflow = bool(routing_block.get("ai_in_hours_overflow", True))
    cr.backup_number = routing_block.get("backup_number")
    cr.ai_sip_uri = routing_block.get("ai_sip_uri")
    cr.dids = list(routing_block.get("dids") or [])
    cr.front_desk_numbers = list(routing_block.get("front_desk_numbers") or [])
    cr.hours = dict(routing_block.get("hours") or {})
    cr.updated_at = datetime.utcnow()


def _coerce_holiday_date(value: Any) -> date:
    """YAML may parse `2026-12-25` as date OR string depending on quoting.
    ClinicClosure.start_date is a Date column, so normalize to datetime.date."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _upsert_holidays(db: Session, clinic_id: str, holidays: list) -> None:
    # Wipe and re-insert: holidays list is authoritative from YAML.
    db.query(ClinicClosure).filter_by(clinic_id=clinic_id, kind="holiday").delete()
    for h in holidays or []:
        d = _coerce_holiday_date(h)
        db.add(ClinicClosure(
            id=f"{clinic_id}:holiday:{d.isoformat()}",
            clinic_id=clinic_id,
            start_date=d,
            end_date=None,
            kind="holiday",
        ))


def _upsert_ai_voice_override(db: Session, clinic_id: str, clinic_data: dict, practice_type_id: str) -> None:
    """Create a clinic_ai_voice row ONLY if product.yaml overrides assistant_name."""
    clinic_block = clinic_data.get("clinic", {})
    pt = db.query(PracticeType).filter_by(id=practice_type_id).one()
    name_in_product = clinic_block.get("assistant_name")
    if not name_in_product or name_in_product == pt.assistant_name:
        return  # no override
    voice = db.query(ClinicAiVoice).filter_by(clinic_id=clinic_id).one_or_none()
    if voice is None:
        voice = ClinicAiVoice(
            clinic_id=clinic_id, assistant_name=name_in_product,
            provider_title="Denturist", reason_question="What brings you in today?",
            language="en",
        )
        db.add(voice)
    voice.assistant_name = name_in_product


def _upsert_ai_disclosure_override(db: Session, clinic_id: str, clinic_data: dict, practice_type_id: str) -> None:
    """Create a clinic_ai_disclosure row ONLY if phrase or required overridden."""
    clinic_block = clinic_data.get("clinic", {})
    pt = db.query(PracticeType).filter_by(id=practice_type_id).one()
    phrase_in_product = clinic_block.get("ai_disclosure_phrase")
    required_in_product = clinic_block.get("ai_disclosure_required")
    if (
        (phrase_in_product is None or phrase_in_product == pt.ai_disclosure_phrase)
        and (required_in_product is None or required_in_product == pt.ai_disclosure_required)
    ):
        return  # no override
    disc = db.query(ClinicAiDisclosure).filter_by(clinic_id=clinic_id).one_or_none()
    if disc is None:
        disc = ClinicAiDisclosure(
            clinic_id=clinic_id,
            required=bool(required_in_product if required_in_product is not None else pt.ai_disclosure_required),
            phrase=str(phrase_in_product or pt.ai_disclosure_phrase),
        )
        db.add(disc)
    if phrase_in_product is not None:
        disc.phrase = phrase_in_product
    if required_in_product is not None:
        disc.required = required_in_product


def seed_from_yaml(db: Session, yaml_dir: Path, clinic_id: Optional[str] = None) -> int:
    """Seed all clinics under yaml_dir (or just `clinic_id` if given).

    Returns the number of clinics processed.
    """
    yaml_dir = Path(yaml_dir)
    if not yaml_dir.exists():
        raise FileNotFoundError(yaml_dir)

    processed = 0
    for clinic_dir in sorted(yaml_dir.iterdir()):
        if not clinic_dir.is_dir() or clinic_dir.name in {"base", "tmp"}:
            continue
        if not (clinic_dir / "product.yaml").exists():
            continue
        if clinic_id and clinic_dir.name != clinic_id:
            continue

        cid = clinic_dir.name
        data = _load_clinic(clinic_dir)
        base_data = _load_base_for(clinic_dir)
        pt_id = _upsert_practice_type(db, base_data, data)
        db.flush()  # ensure PracticeType row exists for FK lookup
        _upsert_clinic_columns(db, cid, data, pt_id)
        db.flush()
        routing = data.get("routing") or {}
        _upsert_routing(db, cid, routing)
        db.flush()
        _upsert_holidays(db, cid, routing.get("holidays") or [])
        _upsert_ai_voice_override(db, cid, data, pt_id)
        _upsert_ai_disclosure_override(db, cid, data, pt_id)
        db.flush()
        processed += 1
        logger.info("Seeded clinic config: %s (practice_type=%s)", cid, pt_id)

    return processed


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yaml-dir", required=True, type=Path,
                        help="Path to packages/shared/config/clinics")
    parser.add_argument("--clinic-id", default=None,
                        help="Seed only this clinic (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Roll back at the end instead of committing")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        n = seed_from_yaml(db, args.yaml_dir, args.clinic_id)
        if args.dry_run:
            db.rollback()
            logger.info("DRY RUN: %d clinic(s) processed, rolled back", n)
        else:
            db.commit()
            logger.info("Committed %d clinic(s)", n)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
