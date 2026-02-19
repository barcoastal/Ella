from fastapi import APIRouter
from app.database import get_db
from app.models import TemplateResponse

router = APIRouter()


@router.get("/templates", response_model=list[TemplateResponse])
def list_templates():
    db = get_db()
    rows = db.execute("SELECT * FROM templates ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]
