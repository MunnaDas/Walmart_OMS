from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageMeta(BaseModel):
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    count: int


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
