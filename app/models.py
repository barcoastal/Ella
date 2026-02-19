from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SlideCreate(BaseModel):
    slide_type: str = "light"
    title: str = ""
    section: str = ""
    body_html: str = ""
    custom_css: str = ""
    position: Optional[int] = None


class SlideUpdate(BaseModel):
    slide_type: Optional[str] = None
    title: Optional[str] = None
    section: Optional[str] = None
    body_html: Optional[str] = None
    custom_css: Optional[str] = None


class SlideResponse(BaseModel):
    id: int
    position: int
    slide_type: str
    title: str
    section: str
    body_html: str
    custom_css: str
    created_at: str
    updated_at: str


class ReorderRequest(BaseModel):
    slide_ids: list[int]


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    slide_type: str
    body_html: str
