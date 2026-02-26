from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings


def _get_db_url() -> str:
    """Normalize DB URL for psycopg3 (psycopg package).
    psycopg3 requires 'postgresql+psycopg://' dialect prefix.
    """
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Already has a dialect prefix like postgresql+psycopg:// — leave as-is
    return url


engine = create_engine(
    _get_db_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    """Create all tables. Called at app startup."""
    import models.user  # noqa
    import models.study_source  # noqa
    import models.quiz_session  # noqa
    import models.quiz_question  # noqa
    import models.user_answer  # noqa
    Base.metadata.create_all(bind=engine)
