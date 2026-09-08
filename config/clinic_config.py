from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ClinicConfig:
    name: str = "Bright Smile Dental Clinic"
    phone_number: str = "+1-555-123-4567"
    address: str = "123 Main Street, Springfield, IL 62701"

    # Business hours (24-hour format)
    business_hours: Dict[str, tuple] = None

    # Insurance providers supported
    supported_insurance: List[str] = None

    # Appointment settings
    min_advance_hours: int = 24  # Minimum hours in advance to book
    max_advance_days: int = 60  # Maximum days in advance to book
    appointment_duration_minutes: int = 30
    max_appointments_per_day: int = 8

    # SMS configuration for escalation
    escalation_sms_enabled: bool = True

    # Escalation contact number
    escalation_phone_number: str = "+1-555-123-4567"

    def __post_init__(self):
        if self.business_hours is None:
            # Monday-Friday: 8am-6pm, Saturday: 9am-2pm, Sunday: Closed
            self.business_hours = {
                "Monday": ("08:00", "18:00"),
                "Tuesday": ("08:00", "18:00"),
                "Wednesday": ("08:00", "18:00"),
                "Thursday": ("08:00", "18:00"),
                "Friday": ("08:00", "18:00"),
                "Saturday": ("09:00", "14:00"),
                "Sunday": None,  # Closed
            }

        if self.supported_insurance is None:
            self.supported_insurance = [
                "Aetna",
                "Blue Cross Blue Shield",
                "Cigna",
                "Delta Dental",
                "Guardian",
                "Humana",
                "MetLife",
                "United Healthcare",
            ]

    def is_open(self, day_name: str, time_str: str) -> bool:
        """Check if clinic is open on given day at given time."""
        if day_name not in self.business_hours:
            return False

        hours = self.business_hours.get(day_name)
        if hours is None:
            return False

        open_time, close_time = hours
        return open_time <= time_str < close_time

    def get_hours_message(self) -> str:
        """Get formatted business hours for voice response."""
        lines = [f"{self.name} hours:"]
        for day, hours in self.business_hours.items():
            if hours:
                open_time, close_time = hours
                lines.append(f"{day}: {open_time} to {close_time}")
            else:
                lines.append(f"{day}: Closed")
        return " ".join(lines)

clinic = ClinicConfig()
