from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.database import init_db, get_db
from app.routers import slides, templates, images, presentation

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Nofar Presentation Manager")

# Mount static directories
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")

# Include routers
app.include_router(slides.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(presentation.router)


@app.on_event("startup")
def startup():
    init_db()
    # Auto-seed if database is empty (first deploy)
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM slides").fetchone()[0]
    db.close()
    if count == 0:
        import subprocess, sys
        subprocess.run([sys.executable, str(BASE_DIR / "seed_db.py")], cwd=str(BASE_DIR))


@app.get("/")
def admin_panel():
    return FileResponse(str(BASE_DIR / "app" / "static" / "admin" / "index.html"))
