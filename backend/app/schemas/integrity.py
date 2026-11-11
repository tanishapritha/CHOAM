from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IntegrityIssueRead(BaseModel):
    code: str
    message: str


class IntegrityReportRead(BaseModel):
    purchase_request_id: UUID
    request_status: str
    request_version: int
    is_valid: bool
    issues: list[IntegrityIssueRead]

    model_config = ConfigDict(from_attributes=True)
