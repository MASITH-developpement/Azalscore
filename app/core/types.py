"""
AZALS - Types SQLAlchemy Universels
====================================
Types compatibles PostgreSQL ET SQLite pour les tests.
"""

import json as json_lib
import logging
import uuid

from sqlalchemy import String, Text, TypeDecorator

logger = logging.getLogger(__name__)
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


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
            # Ensure it's a valid UUID for PostgreSQL
            if isinstance(value, uuid.UUID):
                return value
            try:
                return uuid.UUID(str(value))
            except (ValueError, AttributeError):
                return uuid.uuid4()
        if isinstance(value, uuid.UUID):
            return str(value)
        # Validate string value before storing
        try:
            return str(uuid.UUID(str(value)))
        except (ValueError, AttributeError):
            return str(uuid.uuid4())

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            # Handle corrupted UUID data gracefully
            logger.warning(
                "[TYPES] Valeur UUID corrompue en base — UUID régénéré",
                extra={
                    "corrupted_value": repr(value)[:100],
                    "consequence": "new_uuid_generated"
                }
            )
            return uuid.uuid4()


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


class ARRAY(TypeDecorator):
    """
    Type ARRAY universel compatible PostgreSQL et SQLite.

    - PostgreSQL: Utilise le type ARRAY natif
    - SQLite: Stocke comme Text avec sérialisation JSON

    Usage:
        tags = Column(ARRAY(String), default=list)
        ids = Column(ARRAY(Integer), default=list)
    """

    impl = Text
    cache_ok = True

    def __init__(self, item_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
            return dialect.type_descriptor(PG_ARRAY(self.item_type or String))
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
