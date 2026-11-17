"""Unit tests for SQLite database connectivity and table operations."""

from sqlalchemy import Column, Integer, String, text

from app.core.database import Base, SessionLocal, engine


class MilestoneHealthProbe(Base):
    """Temporary model to verify database read/write connectivity."""

    __tablename__ = "milestone_health_probe"

    id = Column(Integer, primary_key=True, index=True)
    probe_name = Column(String(50), nullable=False)


def test_sqlite_connectivity_and_operations():
    """Verify engine connects, creates tables, writes and reads rows."""
    # Create test table
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Verify simple execution
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1

        # Test insert and query
        probe = MilestoneHealthProbe(probe_name="m1_verification")
        db.add(probe)
        db.commit()
        db.refresh(probe)

        retrieved = (
            db.query(MilestoneHealthProbe)
            .filter_by(probe_name="m1_verification")
            .first()
        )
        assert retrieved is not None
        assert retrieved.probe_name == "m1_verification"

        # Cleanup test row
        db.delete(retrieved)
        db.commit()
    finally:
        db.close()
