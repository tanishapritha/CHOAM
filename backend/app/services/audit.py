from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent


def record_audit_event(
    db: AsyncSession,
    *,
    purchase_request_id: UUID,
    actor_role: str,
    actor_authenticated: bool,
    action: str,
    entity_type: str,
    entity_id: str,
    request_version: int,
    details: dict[str, Any] | None = None,
    source: str = "api",
) -> AuditEvent:
    """Stage a sanitized audit event in the caller's transaction."""
    event = AuditEvent(
        purchase_request_id=purchase_request_id,
        actor_role=actor_role,
        actor_authenticated=actor_authenticated,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        request_version=request_version,
        source=source,
        details=details or {},
    )
    db.add(event)
    return event
