from datetime import date
from database.models import Clinic
from database.v1_1.models import ClinicHoliday


def test_clinic_holiday_round_trips(db_session):
    db_session.add(Clinic(id="c1", name="C1", timezone="America/Edmonton"))
    db_session.commit()
    db_session.add(ClinicHoliday(clinic_id="c1", holiday_date=date(2026, 9, 7), label="Labour Day"))
    db_session.commit()
    rows = db_session.query(ClinicHoliday).filter(ClinicHoliday.clinic_id == "c1").all()
    assert len(rows) == 1
    assert rows[0].holiday_date == date(2026, 9, 7)
    assert rows[0].label == "Labour Day"
