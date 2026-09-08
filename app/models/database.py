from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings

Base = declarative_base()

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=False)
    reason_for_visit = Column(String, nullable=True)
    status = Column(String, default="scheduled", index=True)  # scheduled, cancelled, completed, no-show
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "appointment_date": str(self.appointment_date),
            "appointment_time": str(self.appointment_time),
            "reason_for_visit": self.reason_for_visit,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    intent = Column(String, nullable=True, index=True)
    turn_count = Column(Integer, default=0)
    resolution_status = Column(String, nullable=True, index=True)  # resolved, escalated, error, failed
    escalation_reason = Column(String, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5
    transcript = Column(Text, nullable=True)  # JSON string
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "call_id": self.call_id,
            "phone_number": self.phone_number,
            "timestamp": self.timestamp.isoformat(),
            "intent": self.intent,
            "turn_count": self.turn_count,
            "resolution_status": self.resolution_status,
            "escalation_reason": self.escalation_reason,
            "satisfaction_rating": self.satisfaction_rating,
            "transcript": self.transcript,
            "duration_seconds": self.duration_seconds,
        }


# Database connection
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
