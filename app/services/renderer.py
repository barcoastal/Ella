from pathlib import Path
from app.database import get_db

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def render_presentation(standalone: bool = False) -> str:
    db = get_db()
    slides = db.execute("SELECT * FROM slides ORDER BY position").fetchall()
    db.close()

    css_text = (STATIC_DIR / "presentation.css").read_text(encoding="utf-8")
    js_text = (STATIC_DIR / "presentation.js").read_text(encoding="utf-8")

    # Build slide HTML
    slides_html = []
    for s in slides:
        slide_type = s["slide_type"]
        body = s["body_html"]
        custom_css = s["custom_css"] or ""
        style_tag = f"<style>{custom_css}</style>" if custom_css else ""
        slides_html.append(
            f'{style_tag}<div class="slide slide--{slide_type}">{body}</div>'
        )

    total = len(slides)
    all_slides = "\n".join(slides_html)

    if standalone:
        # For export: inline images would need base64 encoding,
        # but for now we keep relative paths
        img_base = ""
    else:
        img_base = ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nofar Europe - Investor Presentation</title>
<style>
{css_text}
</style>
</head>
<body>
<div class="deck">
{all_slides}
</div>
<div class="nav">
  <button onclick="prev()">&#9664;</button>
  <span class="counter">1 / {total}</span>
  <div class="progress"><div class="progress-bar" style="width:{100/max(total,1):.1f}%"></div></div>
  <button onclick="next()">&#9654;</button>
</div>
<script>
{js_text}
</script>
</body>
</html>"""
    return html
