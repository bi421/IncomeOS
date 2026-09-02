from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional

class Salary(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"

class Location(BaseModel):
    text: str = ""
    country: str = ""
    remote: bool = False

class JobOffer(BaseModel):
    source: str
    title: str
    company: str
    url: HttpUrl
    salary: Optional[Salary] = None
    location: Location
    description: str
    created_at: str
    raw_data: dict

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v
