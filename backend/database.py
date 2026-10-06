"""Motor SQLAlchemy, sesión y Base declarativa.

Las tablas de PostgreSQL ya existen; este módulo NO crea ni recrea esquema
alguno (nunca se llama a ``Base.metadata.create_all``).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import DATABASE_URL

# ``future=True`` mantiene compatibilidad con el estilo 2.x de SQLAlchemy.
engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Clase base declarativa de la que heredan todos los modelos ORM.
Base = declarative_base()


def get_db():
    """Generador de sesión para dependencias de FastAPI u otros consumidores."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
