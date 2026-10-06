"""Configuración de conexión a PostgreSQL (Sprint 1).

Cadena de conexión oficial del entorno de desarrollo:

    postgresql://pas_owner:29/t(f8Q$c9C@127.0.0.1:5432/pas_data

Nota sobre la contraseña: contiene caracteres especiales (``/``, ``(``, ``)``).
La URL cruda es válida para SQLAlchemy porque el delimitador ``@`` aparece
después de la contraseña. Aun así, se expone ``DATABASE_URL_ENCODED`` con la
contraseña codificada (``quote_plus``) como alternativa robusta.

Los valores pueden sobreescribirse mediante variables de entorno
(``DB_USER``, ``DB_PASSWORD``, ``DB_HOST``, ``DB_PORT``, ``DB_NAME``).
"""

import os
from urllib.parse import quote_plus

DB_USER = os.getenv("DB_USER", "pas_owner")
DB_PASSWORD = os.getenv("DB_PASSWORD", "29/t(f8Q$c9C")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pas_data")

# Cadena de conexión solicitada en el sprint.
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Variante con la contraseña codificada para URL (más robusta ante caracteres especiales).
DATABASE_URL_ENCODED = (
    f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
