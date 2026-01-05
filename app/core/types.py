"""
AZALS - Types SQLAlchemy Universels
====================================
Types compatibles PostgreSQL ET SQLite pour les tests.
"""

import uuid
import json as json_lib
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB


class UniversalUUID(TypeDecorator):
    """
    Type UUID universel compatible PostgreSQL et SQLite.

    - PostgreSQL: Utilise le type UUID natif
    - SQLite: Stocke comme String(36)

    Usage:
        id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class JSON(TypeDecorator):
    """
    Type JSON universel compatible PostgreSQL et SQLite.

    - PostgreSQL: Utilise le type JSON natif
    - SQLite: Stocke comme Text avec sérialisation JSON

    Usage:
        data = Column(JSON, default=dict)
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        return json_lib.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        if isinstance(value, str):
            return json_lib.loads(value)
        return value


class JSONB(TypeDecorator):
    """
    Type JSONB universel compatible PostgreSQL et SQLite.

    - PostgreSQL: Utilise le type JSONB natif (indexable)
    - SQLite: Stocke comme Text avec sérialisation JSON

    Usage:
        metadata = Column(JSONB, default=dict)
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        return json_lib.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        if isinstance(value, str):
            return json_lib.loads(value)
        return value
