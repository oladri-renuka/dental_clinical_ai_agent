import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import init_db, SessionLocal, Appointment, engine, Base
from sqlalchemy import inspect

def seed_appointments():
    """Create 20 pre-populated appointments spanning next 30 days."""
    db = SessionLocal()

    # Check if appointments already exist
    existing = db.query(Appointment).count()
    if existing > 0:
        print(f"Database already has {existing} appointments. Skipping seed.")
        db.close()
        return

    today = datetime.now().date()
    reasons = [
        "Regular cleaning",
        "Dental exam",
        "Root canal",
        "Crown placement",
        "Teeth whitening",
        "Cavity filling",
        "Wisdom tooth extraction",
        "Emergency dental care",
    ]

    names = [
        "John Smith",
        "Sarah Johnson",
        "Michael Brown",
        "Emily Davis",
        "Robert Wilson",
        "Jennifer Garcia",
        "David Martinez",
        "Lisa Anderson",
        "James Taylor",
        "Maria Thomas",
    ]

    # Create 20 appointments
    appointments = []
    for i in range(20):
        # Spread appointments across next 30 days
        appointment_date = today + timedelta(days=(i % 25) + 1)

        # Alternate between morning and afternoon slots
        if i % 2 == 0:
            appointment_time = "09:00"  # 9 AM
        else:
            appointment_time = "14:00"  # 2 PM

        appointment = Appointment(
            patient_name=names[i % len(names)],
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason_for_visit=reasons[i % len(reasons)],
            status="scheduled" if i < 18 else "cancelled",  # Last 2 are cancelled
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        appointments.append(appointment)

    db.add_all(appointments)
    db.commit()
    print(f"✅ Seeded {len(appointments)} appointments")
    db.close()


def init_database():
    """Initialize database and seed data."""
    print("🔧 Initializing database...")

    # Create tables
    init_db()
    print("✅ Database tables created")

    # Check if tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📋 Tables in database: {tables}")

    # Seed data
    seed_appointments()

    print("✅ Database initialization complete!")


if __name__ == "__main__":
    init_database()
