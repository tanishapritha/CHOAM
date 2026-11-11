from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    id: UUID
    purchase_request_id: UUID
    actor_role: str
    actor_authenticated: bool
    action: str
    entity_type: str
    entity_id: str
    request_version: int
    source: str
    details: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
