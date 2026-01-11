"""
AZALS - SystemSettings Model
============================
Global system-level settings (not per-tenant).
Used for platform-wide configuration like bootstrap locking.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.core.types import JSON, UniversalUUID


class SystemSettings(Base):
    """
    Global system settings (singleton-like model).

    This model stores platform-wide configuration that applies
    to the entire AZALS system, not individual tenants.

    Key settings:
    - bootstrap_locked: Prevents re-running initial setup
    - maintenance_mode: Platform-wide maintenance flag
    - platform_version: Current deployment version
    """
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UniversalUUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True
    )

    # Bootstrap control - CRITICAL
    bootstrap_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Once True, initial setup cannot be re-run"
    )

    # Platform status
    maintenance_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Platform-wide maintenance mode"
    )
    maintenance_message: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Message displayed during maintenance"
    )

    # Version tracking
    platform_version: Mapped[str] = mapped_column(
        String(20),
        default="1.0.0",
        nullable=False
    )

    # Feature flags (global)
    demo_mode_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Enable demo/cockpit mode"
    )

    registration_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Allow new tenant registration"
    )

    # Rate limits (global defaults)
    global_api_rate_limit: Mapped[int] = mapped_column(
        Integer,
        default=10000,
        nullable=False,
        comment="Platform-wide API rate limit per hour"
    )

    # Additional settings as JSON
    extra_settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional settings as key-value pairs"
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    updated_by: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="User/system that made the last change"
    )


__all__ = ["SystemSettings"]
