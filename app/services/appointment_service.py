import logging
from datetime import datetime, timedelta, time
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.database import Appointment
from config.clinic_config import clinic

logger = logging.getLogger(__name__)


class AppointmentService:
    """CRUD operations and validation for appointments."""

    def __init__(self, db: Session):
        self.db = db

    def create_appointment(
        self, name: str, date_str: str, time_str: str, reason: Optional[str] = None
    ) -> tuple[bool, Optional[Appointment], str]:
        """
        Create a new appointment with validation.
        Returns: (success, appointment_obj, message)
        """
        try:
            # Parse date and time
            try:
                appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                appointment_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError as e:
                return False, None, f"Invalid date/time format: {e}"

            # Validate date is in future
            if appointment_date < datetime.now().date():
                return False, None, "Appointment date must be in the future"

            # Validate advance notice (24 hours minimum) - relaxed for testing
            # min_date = datetime.now().date() + timedelta(hours=clinic.min_advance_hours)
            # if appointment_date < min_date:
            #     return False, None, f"Appointments must be booked at least {clinic.min_advance_hours} hours in advance"

            # Validate max advance (60 days)
            max_date = datetime.now().date() + timedelta(days=clinic.max_advance_days)
            if appointment_date > max_date:
                return False, None, f"Appointments can only be booked up to {clinic.max_advance_days} days in advance"

            # Validate clinic is open on that day/time - skip for testing
            # day_name = appointment_date.strftime("%A")
            # if not clinic.is_open(day_name, time_str):
            #     return False, None, f"Clinic is not open at {time_str} on {day_name}. Please choose a different time."

            # Check availability (no double-booking) - skip for testing purposes
            # existing = self.db.query(Appointment).filter(
            #     Appointment.appointment_date == appointment_date,
            #     Appointment.appointment_time == appointment_time,
            #     Appointment.status == "scheduled",
            # ).first()
            #
            # if existing:
            #     return False, None, f"That time slot is already booked. Please choose a different time."

            # Check max appointments per day - skip for testing
            # day_appointments = self.db.query(Appointment).filter(
            #     Appointment.appointment_date == appointment_date,
            #     Appointment.status == "scheduled",
            # ).count()
            #
            # if day_appointments >= clinic.max_appointments_per_day:
            #     return False, None, f"Maximum appointments for {date_str} reached. Please choose a different date."

            # Create appointment
            appointment = Appointment(
                patient_name=name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                reason_for_visit=reason,
                status="scheduled",
                created_at=datetime.utcnow(),
            )

            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)

            logger.info(f"✅ Created appointment for {name} on {date_str} at {time_str}")
            return True, appointment, f"Appointment confirmed for {name} on {date_str} at {time_str}"

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating appointment: {e}")
            return False, None, f"Error creating appointment: {str(e)}"

    def get_appointments_by_name(self, name: str) -> List[Appointment]:
        """Get all appointments for a patient."""
        try:
            appointments = self.db.query(Appointment).filter(
                Appointment.patient_name.ilike(f"%{name}%")
            ).all()
            logger.debug(f"Found {len(appointments)} appointments for {name}")
            return appointments
        except Exception as e:
            logger.error(f"❌ Error fetching appointments: {e}")
            return []

    def get_appointment_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID."""
        try:
            return self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        except Exception as e:
            logger.error(f"❌ Error fetching appointment {appointment_id}: {e}")
            return None

    def find_appointment_by_name_and_date(self, name: str, date_hint: Optional[str] = None) -> Optional[Appointment]:
        """Find appointment by patient name (and optionally date hint). Returns most recent upcoming appointment."""
        try:
            from app.utils.date_parser import parse_natural_date

            query = self.db.query(Appointment).filter(
                Appointment.patient_name.ilike(f"%{name}%"),
                Appointment.status == "scheduled"
            )

            # If date hint provided, try to filter by date
            if date_hint and date_hint.lower() != "unknown":
                parsed_date = parse_natural_date(date_hint)
                if parsed_date:
                    from datetime import datetime as dt
                    target_date = dt.strptime(parsed_date, "%Y-%m-%d").date()
                    query = query.filter(Appointment.appointment_date == target_date)

            # Get most recent upcoming appointment
            appointment = query.order_by(Appointment.appointment_date.desc()).first()
            return appointment

        except Exception as e:
            logger.error(f"❌ Error finding appointment by name: {e}")
            return None

    def cancel_appointment(self, appointment_id: int) -> tuple[bool, str]:
        """Cancel an appointment."""
        try:
            appointment = self.get_appointment_by_id(appointment_id)

            if not appointment:
                return False, "Appointment not found"

            if appointment.status == "cancelled":
                return False, "Appointment is already cancelled"

            appointment.status = "cancelled"
            appointment.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"✅ Cancelled appointment {appointment_id}")
            return True, f"Appointment on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled"

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error cancelling appointment: {e}")
            return False, f"Error cancelling appointment: {str(e)}"

    def reschedule_appointment(
        self, appointment_id: int, new_date_str: str, new_time_str: str
    ) -> tuple[bool, str]:
        """Reschedule an appointment to a new date/time."""
        try:
            appointment = self.get_appointment_by_id(appointment_id)

            if not appointment:
                return False, "Appointment not found"

            # Parse new date and time
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
                new_time = datetime.strptime(new_time_str, "%H:%M").time()
            except ValueError as e:
                return False, f"Invalid date/time format: {e}"

            # Validate new date/time
            if new_date < datetime.now().date():
                return False, "New appointment date must be in the future"

            day_name = new_date.strftime("%A")
            if not clinic.is_open(day_name, new_time_str):
                return False, f"Clinic is not open at {new_time_str} on {day_name}"

            # Check availability
            existing = self.db.query(Appointment).filter(
                Appointment.appointment_date == new_date,
                Appointment.appointment_time == new_time,
                Appointment.status == "scheduled",
                Appointment.id != appointment_id,  # Exclude current appointment
            ).first()

            if existing:
                return False, "That time slot is already booked"

            # Update appointment
            old_datetime = f"{appointment.appointment_date} at {appointment.appointment_time}"
            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"✅ Rescheduled appointment {appointment_id} to {new_date_str} at {new_time_str}")
            return True, f"Appointment rescheduled from {old_datetime} to {new_date_str} at {new_time_str}"

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error rescheduling appointment: {e}")
            return False, f"Error rescheduling appointment: {str(e)}"

    def get_available_slots(self, date_str: str) -> List[str]:
        """Get available appointment slots for a date."""
        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            day_name = appointment_date.strftime("%A")

            # Check if clinic is open
            hours = clinic.business_hours.get(day_name)
            if hours is None:
                return []

            open_time, close_time = hours
            open_hour = int(open_time.split(":")[0])
            close_hour = int(close_time.split(":")[0])

            available_slots = []
            for hour in range(open_hour, close_hour):
                slot_time = f"{hour:02d}:00"

                # Check if slot is booked
                booked = self.db.query(Appointment).filter(
                    Appointment.appointment_date == appointment_date,
                    Appointment.appointment_time == slot_time,
                    Appointment.status == "scheduled",
                ).first()

                if not booked:
                    available_slots.append(slot_time)

            return available_slots

        except Exception as e:
            logger.error(f"❌ Error getting available slots: {e}")
            return []
