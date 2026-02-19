from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import SlideCreate, SlideUpdate, SlideResponse, ReorderRequest

router = APIRouter()


def row_to_dict(row) -> dict:
    return dict(row)


@router.get("/slides", response_model=list[SlideResponse])
def list_slides():
    db = get_db()
    rows = db.execute("SELECT * FROM slides ORDER BY position").fetchall()
    db.close()
    return [row_to_dict(r) for r in rows]


@router.get("/slides/{slide_id}", response_model=SlideResponse)
def get_slide(slide_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM slides WHERE id = ?", (slide_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Slide not found")
    return row_to_dict(row)


@router.post("/slides", response_model=SlideResponse, status_code=201)
def create_slide(slide: SlideCreate):
    db = get_db()
    if slide.position is None:
        max_pos = db.execute("SELECT COALESCE(MAX(position), 0) FROM slides").fetchone()[0]
        position = max_pos + 1
    else:
        position = slide.position
        # Shift slides at or after this position
        db.execute("UPDATE slides SET position = position + 1 WHERE position >= ?", (position,))

    cursor = db.execute(
        """INSERT INTO slides (position, slide_type, title, section, body_html, custom_css)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (position, slide.slide_type, slide.title, slide.section, slide.body_html, slide.custom_css),
    )
    db.commit()
    row = db.execute("SELECT * FROM slides WHERE id = ?", (cursor.lastrowid,)).fetchone()
    db.close()
    return row_to_dict(row)


@router.put("/slides/{slide_id}", response_model=SlideResponse)
def update_slide(slide_id: int, slide: SlideUpdate):
    db = get_db()
    existing = db.execute("SELECT * FROM slides WHERE id = ?", (slide_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(status_code=404, detail="Slide not found")

    updates = {}
    for field in ("slide_type", "title", "section", "body_html", "custom_css"):
        val = getattr(slide, field)
        if val is not None:
            updates[field] = val

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        values = list(updates.values()) + [slide_id]
        db.execute(f"UPDATE slides SET {set_clause} WHERE id = ?", values)
        db.commit()

    row = db.execute("SELECT * FROM slides WHERE id = ?", (slide_id,)).fetchone()
    db.close()
    return row_to_dict(row)


@router.delete("/slides/{slide_id}")
def delete_slide(slide_id: int):
    db = get_db()
    existing = db.execute("SELECT * FROM slides WHERE id = ?", (slide_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(status_code=404, detail="Slide not found")

    pos = existing["position"]
    db.execute("DELETE FROM slides WHERE id = ?", (slide_id,))
    db.execute("UPDATE slides SET position = position - 1 WHERE position > ?", (pos,))
    db.commit()
    db.close()
    return {"ok": True}


@router.patch("/slides/reorder")
def reorder_slides(req: ReorderRequest):
    db = get_db()
    for i, sid in enumerate(req.slide_ids):
        db.execute("UPDATE slides SET position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (i + 1, sid))
    db.commit()
    db.close()
    return {"ok": True}


@router.post("/slides/{slide_id}/duplicate", response_model=SlideResponse, status_code=201)
def duplicate_slide(slide_id: int):
    db = get_db()
    original = db.execute("SELECT * FROM slides WHERE id = ?", (slide_id,)).fetchone()
    if not original:
        db.close()
        raise HTTPException(status_code=404, detail="Slide not found")

    new_pos = original["position"] + 1
    # Shift subsequent slides
    db.execute("UPDATE slides SET position = position + 1 WHERE position >= ?", (new_pos,))

    cursor = db.execute(
        """INSERT INTO slides (position, slide_type, title, section, body_html, custom_css)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (new_pos, original["slide_type"], original["title"] + " (Copy)",
         original["section"], original["body_html"], original["custom_css"]),
    )
    db.commit()
    row = db.execute("SELECT * FROM slides WHERE id = ?", (cursor.lastrowid,)).fetchone()
    db.close()
    return row_to_dict(row)
