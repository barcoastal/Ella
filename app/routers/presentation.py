from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.services.renderer import render_presentation

router = APIRouter()


@router.get("/presentation", response_class=HTMLResponse)
def view_presentation():
    return render_presentation()


@router.get("/presentation/export", response_class=HTMLResponse)
def export_presentation():
    return render_presentation(standalone=True)
