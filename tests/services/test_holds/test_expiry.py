from datetime import datetime, date, time
import pytz
from database.models import Clinic
from database.v1_1.models import ClinicOperatingHours, ClinicHoliday
from services.holds import compute_hold_expiry

TZ = pytz.timezone("America/Edmonton")


def _seed_market_mall(db):
    db.add(Clinic(id="mm", name="MM", timezone="America/Edmonton"))
    hours = [(0, 9, 0, 17, 0), (1, 9, 0, 17, 0), (2, 9, 0, 17, 0), (3, 9, 0, 17, 0), (4, 9, 0, 18, 30)]
    for dow, oh, om, ch, cm in hours:
        db.add(ClinicOperatingHours(clinic_id="mm", day_of_week=dow,
                                    open_at=time(oh, om), close_at=time(ch, cm), is_closed=False))
    for dow in (5, 6):
        db.add(ClinicOperatingHours(clinic_id="mm", day_of_week=dow,
                                    open_at=time(0, 0), close_at=time(0, 0), is_closed=True))
    db.commit()


def _expiry_local(db, y, mo, d, h, mi):
    created_utc = TZ.localize(datetime(y, mo, d, h, mi)).astimezone(pytz.utc).replace(tzinfo=None)
    clinic = db.query(Clinic).get("mm")
    exp_naive_utc = compute_hold_expiry(db, clinic, created_utc)
    return pytz.utc.localize(exp_naive_utc).astimezone(TZ)


def test_tuesday_holds_until_wednesday_close(db_session):
    _seed_market_mall(db_session)
    exp = _expiry_local(db_session, 2026, 6, 9, 10, 0)  # Tue 2026-06-09
    assert exp.date() == date(2026, 6, 10) and exp.hour == 17

def test_friday_holds_until_monday_close(db_session):
    _seed_market_mall(db_session)
    exp = _expiry_local(db_session, 2026, 6, 12, 14, 0)  # Fri 2026-06-12
    assert exp.date() == date(2026, 6, 15) and exp.hour == 17

def test_friday_with_monday_holiday_holds_until_tuesday(db_session):
    _seed_market_mall(db_session)
    db_session.add(ClinicHoliday(clinic_id="mm", holiday_date=date(2026, 6, 15), label="Test"))
    db_session.commit()
    exp = _expiry_local(db_session, 2026, 6, 12, 14, 0)
    assert exp.date() == date(2026, 6, 16) and exp.hour == 17

def test_saturday_holds_until_monday_close(db_session):
    _seed_market_mall(db_session)
    exp = _expiry_local(db_session, 2026, 6, 13, 11, 0)  # Sat
    assert exp.date() == date(2026, 6, 15) and exp.hour == 17
