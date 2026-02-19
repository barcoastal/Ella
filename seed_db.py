"""
Seed the database from the existing index.html presentation.
Parses all 38 slides and inserts them into the SQLite database.
Also seeds 10 templates for creating new slides.
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup
from app.database import get_db, init_db, DB_PATH

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "index.html"


def extract_title(slide_div, slide_type: str) -> str:
    """Extract a human-readable title from slide HTML."""
    if slide_type == "dark":
        h1 = slide_div.find("h1")
        if h1:
            return h1.get_text(strip=True)
    else:
        h2 = slide_div.find("h2")
        if h2:
            return h2.get_text(strip=True)
    return ""


def extract_section(slide_div, slide_type: str) -> str:
    """Extract section badge text from dark divider slides."""
    if slide_type == "dark":
        badge = slide_div.find(class_="divider-badge")
        if badge:
            return badge.get_text(strip=True)
    return ""


def seed_slides():
    """Parse index.html and seed all slides into the database."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    deck = soup.find(class_="deck")
    if not deck:
        print("ERROR: Could not find .deck element in index.html")
        return

    slide_divs = deck.find_all("div", class_="slide", recursive=False)
    print(f"Found {len(slide_divs)} slides in index.html")

    db = get_db()
    # Clear existing slides
    db.execute("DELETE FROM slides")

    for i, slide_div in enumerate(slide_divs, start=1):
        classes = slide_div.get("class", [])
        if "slide--dark" in classes:
            slide_type = "dark"
        else:
            slide_type = "light"

        title = extract_title(slide_div, slide_type)
        section = extract_section(slide_div, slide_type)
        # Get inner HTML (everything inside the slide div)
        body_html = slide_div.decode_contents()

        db.execute(
            """INSERT INTO slides (position, slide_type, title, section, body_html, custom_css)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (i, slide_type, title, section, body_html, ""),
        )
        print(f"  Slide {i}: [{slide_type}] {title[:60] or '(no title)'}")

    db.commit()
    db.close()
    print(f"\nSeeded {len(slide_divs)} slides successfully.")


def seed_templates():
    """Seed slide templates for the admin panel."""
    templates = [
        {
            "name": "Dark Divider",
            "description": "Full-screen section divider with badge, title, subtitle",
            "slide_type": "dark",
            "body_html": """  <div class="divider-badge">SECTION</div>
  <h1>Section <span class="accent">Title</span></h1>
  <p class="subtitle">Brief description of this section</p>
  <div class="divider-line"></div>""",
        },
        {
            "name": "Bullet List",
            "description": "Content slide with header and bullet points",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Slide Title</h2>
    <span class="tag">Tag</span>
  </div>
  <div class="content-grid content-grid--2">
    <div class="card">
      <h3>Card Title</h3>
      <ul class="bullet-list">
        <li><strong>Key point one</strong> with supporting detail</li>
        <li><strong>Key point two</strong> with supporting detail</li>
        <li><strong>Key point three</strong> with supporting detail</li>
      </ul>
    </div>
    <div class="card">
      <h3>Card Title</h3>
      <ul class="bullet-list">
        <li><strong>Key point one</strong> with supporting detail</li>
        <li><strong>Key point two</strong> with supporting detail</li>
        <li><strong>Key point three</strong> with supporting detail</li>
      </ul>
    </div>
  </div>""",
        },
        {
            "name": "Two Column",
            "description": "Two-column layout with cards",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Two Columns</h2>
  </div>
  <div class="content-grid content-grid--2">
    <div class="card">
      <h3>Left Column</h3>
      <p class="text-sm" style="color:var(--text-secondary)">Content for the left column goes here.</p>
    </div>
    <div class="card">
      <h3>Right Column</h3>
      <p class="text-sm" style="color:var(--text-secondary)">Content for the right column goes here.</p>
    </div>
  </div>""",
        },
        {
            "name": "Sidebar Layout",
            "description": "Main content with dark sidebar",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Sidebar Layout</h2>
    <span class="tag">Overview</span>
  </div>
  <div class="content-grid content-grid--sidebar">
    <div class="card">
      <h3>Main Content</h3>
      <ul class="bullet-list">
        <li><strong>Point one</strong></li>
        <li><strong>Point two</strong></li>
      </ul>
    </div>
    <div class="sidebar-dark">
      <h3>Key Metrics</h3>
      <div style="margin-bottom:1rem">
        <div class="stat-value">€100M</div>
        <div class="stat-label">Revenue</div>
      </div>
      <div>
        <div class="stat-value">25%</div>
        <div class="stat-label">Growth</div>
      </div>
    </div>
  </div>""",
        },
        {
            "name": "Data Table",
            "description": "Slide with a styled data table",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Data Table</h2>
  </div>
  <table class="data-table">
    <thead>
      <tr><th>Column 1</th><th>Column 2</th><th>Column 3</th><th>Column 4</th></tr>
    </thead>
    <tbody>
      <tr><td>Row 1</td><td class="num">100</td><td class="num">200</td><td class="num">300</td></tr>
      <tr><td>Row 2</td><td class="num">150</td><td class="num">250</td><td class="num">350</td></tr>
      <tr><td><strong>Total</strong></td><td class="num highlight">250</td><td class="num highlight">450</td><td class="num highlight">650</td></tr>
    </tbody>
  </table>""",
        },
        {
            "name": "KPI Dashboard",
            "description": "Stat boxes with key performance indicators",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> KPI Dashboard</h2>
  </div>
  <div class="stat-row mb-1">
    <div class="stat-box">
      <div class="stat-value">€441M</div>
      <div class="stat-label">EBITDA</div>
    </div>
    <div class="stat-box stat-box--accent">
      <div class="stat-value">€3.3B</div>
      <div class="stat-label">Gross Asset Value</div>
    </div>
    <div class="stat-box">
      <div class="stat-value">€1.9B</div>
      <div class="stat-label">Equity Value</div>
    </div>
  </div>
  <div class="kpi-strip">
    <div class="kpi-item"><div class="kpi-val">8</div><div class="kpi-label">Countries</div></div>
    <div class="kpi-item"><div class="kpi-val">3.5 GW</div><div class="kpi-label">Capacity</div></div>
    <div class="kpi-item"><div class="kpi-val">45%</div><div class="kpi-label">LTV</div></div>
  </div>""",
        },
        {
            "name": "Phase Timeline",
            "description": "Timeline with phase cards",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Phase Timeline</h2>
  </div>
  <div class="content-grid content-grid--3">
    <div class="phase-card">
      <div class="phase-num">Phase 1 &middot; 2026</div>
      <h3>Foundation</h3>
      <ul class="bullet-list">
        <li>First milestone</li>
        <li>Second milestone</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-num">Phase 2 &middot; 2027</div>
      <h3>Growth</h3>
      <ul class="bullet-list">
        <li>First milestone</li>
        <li>Second milestone</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-num">Phase 3 &middot; 2028</div>
      <h3>Scale</h3>
      <ul class="bullet-list">
        <li>First milestone</li>
        <li>Second milestone</li>
      </ul>
    </div>
  </div>""",
        },
        {
            "name": "Team Grid",
            "description": "Team members in columns",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Team</h2>
  </div>
  <div class="content-grid content-grid--3">
    <div class="team-section">
      <h4>Department A</h4>
      <div class="team-member">
        <div class="name">John Doe</div>
        <div class="role">Title</div>
        <div class="bio">Brief bio description</div>
      </div>
    </div>
    <div class="team-section">
      <h4>Department B</h4>
      <div class="team-member">
        <div class="name">Jane Smith</div>
        <div class="role">Title</div>
        <div class="bio">Brief bio description</div>
      </div>
    </div>
    <div class="team-section">
      <h4>Department C</h4>
      <div class="team-member">
        <div class="name">Bob Wilson</div>
        <div class="role">Title</div>
        <div class="bio">Brief bio description</div>
      </div>
    </div>
  </div>""",
        },
        {
            "name": "Value Chain",
            "description": "Horizontal process chain with arrow steps",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Value Chain</h2>
  </div>
  <div class="chain-row">
    <div class="chain-step">
      <div class="step-icon">🔧</div>
      <div class="step-title">Step 1</div>
      <div class="step-desc">Description of this step in the process</div>
    </div>
    <div class="chain-step">
      <div class="step-icon">🏗️</div>
      <div class="step-title">Step 2</div>
      <div class="step-desc">Description of this step in the process</div>
    </div>
    <div class="chain-step">
      <div class="step-icon">💰</div>
      <div class="step-title">Step 3</div>
      <div class="step-desc">Description of this step in the process</div>
    </div>
    <div class="chain-step">
      <div class="step-icon">⚡</div>
      <div class="step-title">Step 4</div>
      <div class="step-desc">Description of this step in the process</div>
    </div>
  </div>""",
        },
        {
            "name": "Case Study",
            "description": "Project case study with metrics and details",
            "slide_type": "light",
            "body_html": """  <div class="slide-header">
    <h2><span class="brand">Nofar</span> Case Study</h2>
    <span class="tag">Case Study</span>
  </div>
  <div class="content-grid content-grid--sidebar">
    <div>
      <div class="card mb-1">
        <h3>Project Overview</h3>
        <ul class="bullet-list">
          <li><strong>Location:</strong> Country</li>
          <li><strong>Technology:</strong> Solar PV + BESS</li>
          <li><strong>Capacity:</strong> 100 MW</li>
        </ul>
      </div>
      <div class="card">
        <h3>Value Creation</h3>
        <ul class="bullet-list">
          <li><strong>Investment:</strong> €50M</li>
          <li><strong>Return:</strong> 25% IRR</li>
        </ul>
      </div>
    </div>
    <div class="sidebar-dark">
      <h3>Key Metrics</h3>
      <div style="margin-bottom:1rem">
        <div class="stat-value">€50M</div>
        <div class="stat-label">Invested</div>
      </div>
      <div style="margin-bottom:1rem">
        <div class="stat-value">25%</div>
        <div class="stat-label">IRR</div>
      </div>
      <div>
        <div class="stat-value">2.5x</div>
        <div class="stat-label">MOIC</div>
      </div>
    </div>
  </div>""",
        },
    ]

    db = get_db()
    db.execute("DELETE FROM templates")
    for t in templates:
        db.execute(
            "INSERT INTO templates (name, description, slide_type, body_html) VALUES (?, ?, ?, ?)",
            (t["name"], t["description"], t["slide_type"], t["body_html"]),
        )
    db.commit()
    db.close()
    print(f"Seeded {len(templates)} templates.")


if __name__ == "__main__":
    # Remove existing DB to start fresh
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database.")

    init_db()
    print("Initialized database.\n")

    seed_slides()
    print()
    seed_templates()
    print("\nDone! Run: uvicorn app.main:app --reload")
