"""User → clinic membership join (Firebase UID → clinic_id, many-to-many)."""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, PrimaryKeyConstraint

from database.connection import Base


class UserClinicMembership(Base):
    """Which clinics a given Firebase user is authorized to act on.

    A user may belong to N clinics. Server-side authorization derives the
    allowed set from this table, never from a client header. The
    `email` column is denormalized for audit/UX so admin tooling does
    not have to round-trip through the Firebase Admin SDK.
    """

    __tablename__ = "user_clinic_memberships"

    uid = Column(String(128), nullable=False)
    clinic_id = Column(
        String(64),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
    )
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("uid", "clinic_id", name="pk_user_clinic_memberships"),
        Index("idx_memberships_uid", "uid"),
    )
