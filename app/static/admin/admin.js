// ── State ──
let slides = [];
let currentSlideId = null;
let currentSlide = null;
let templates = [];
let activeTab = 'fields';

const API = '/api';

// ── DOM Refs ──
const slideListEl = document.getElementById('slide-list');
const slideCountEl = document.getElementById('slide-count');
const editorEmpty = document.getElementById('editor-empty');
const editorContent = document.getElementById('editor-content');
const editType = document.getElementById('edit-type');
const fieldsPanel = document.getElementById('editor-fields');
const htmlEditor = document.getElementById('html-editor');
const previewFrame = document.getElementById('preview-frame');
const modalTemplates = document.getElementById('modal-templates');
const templateGrid = document.getElementById('template-grid');

// ── Editable element selectors (order matters - more specific first) ──
const FIELD_DEFS = [
  { sel: '.divider-badge', label: 'Badge', input: 'input' },
  { sel: '.subtitle', label: 'Subtitle', input: 'input' },
  { sel: '.slide-header h2', label: 'Slide Title', input: 'input', special: 'light-title' },
  { sel: '.slide-header .tag', label: 'Tag', input: 'input' },
  { sel: 'h1', label: 'Title', input: 'input', special: 'dark-title' },
  { sel: 'h3', label: 'Heading', input: 'input' },
  { sel: 'h4', label: 'Subheading', input: 'input' },
  { sel: '.phase-num', label: 'Phase', input: 'input' },
  { sel: '.step-title', label: 'Step Title', input: 'input' },
  { sel: '.step-desc', label: 'Step Desc', input: 'textarea' },
  { sel: '.stat-value', label: 'Value', input: 'input' },
  { sel: '.stat-label', label: 'Label', input: 'input' },
  { sel: '.kpi-val', label: 'KPI Value', input: 'input' },
  { sel: '.kpi-label', label: 'KPI Label', input: 'input' },
  { sel: '.name', label: 'Name', input: 'input' },
  { sel: '.role', label: 'Role', input: 'input' },
  { sel: '.bio', label: 'Bio', input: 'textarea' },
  { sel: '.country-name', label: 'Country', input: 'input' },
  { sel: '.country-flag', label: 'Flag', input: 'input' },
  { sel: '.bullet-list > li', label: 'Bullet', input: 'input' },
  { sel: 'thead th', label: 'Column', input: 'input' },
  { sel: 'tbody td', label: 'Cell', input: 'input' },
  { sel: 'p.footnote', label: 'Footnote', input: 'input' },
  { sel: 'p:not(.subtitle):not(.footnote)', label: 'Text', input: 'textarea' },
];

// ── Init ──
document.addEventListener('DOMContentLoaded', async () => {
  initTabs();
  initEventListeners();
  await loadSlides();
  await loadTemplates();
});

// ── Tabs ──
function initTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeTab = tab.dataset.tab;
      document.getElementById('tab-fields').style.display = activeTab === 'fields' ? '' : 'none';
      document.getElementById('tab-html').style.display = activeTab === 'html' ? '' : 'none';
      if (activeTab === 'html' && currentSlide) {
        // Sync fields -> HTML when switching to HTML tab
        htmlEditor.value = collectFieldsToHTML();
      }
      if (activeTab === 'fields' && currentSlide) {
        // Re-parse HTML when switching back to fields tab
        const html = htmlEditor.value;
        renderFieldsFromHTML(html, editType.value);
      }
    });
  });
}

// ── Event Listeners ──
function initEventListeners() {
  document.getElementById('btn-new').addEventListener('click', openTemplateModal);
  document.getElementById('btn-save').addEventListener('click', saveSlide);
  document.getElementById('btn-delete').addEventListener('click', deleteSlide);
  document.getElementById('btn-duplicate').addEventListener('click', duplicateSlide);
  document.getElementById('btn-export').addEventListener('click', exportPresentation);
  document.getElementById('btn-add-text').addEventListener('click', addTextBlock);
  document.getElementById('btn-add-bullet').addEventListener('click', addBulletBlock);
  editType.addEventListener('change', () => {
    if (currentSlide) schedulePreview();
  });

  // Modal close
  document.querySelectorAll('.modal__overlay, .modal__close').forEach(el => {
    el.addEventListener('click', () => { modalTemplates.style.display = 'none'; });
  });

  // Ctrl+S to save
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      if (currentSlideId) saveSlide();
    }
  });
}

// ── API ──
async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Slide List ──
async function loadSlides() {
  slides = await api('/slides');
  renderSlideList();
}

function renderSlideList() {
  slideCountEl.textContent = slides.length;
  slideListEl.innerHTML = slides.map((s, i) => `
    <div class="slide-item ${s.id === currentSlideId ? 'active' : ''}" data-id="${s.id}">
      <span class="slide-item__drag" title="Drag to reorder">&#9776;</span>
      <span class="slide-item__num">${i + 1}</span>
      <div class="slide-item__info">
        <div class="slide-item__title">${esc(s.title || '(untitled)')}</div>
      </div>
      <span class="slide-item__type slide-item__type--${s.slide_type}">${s.slide_type}</span>
    </div>
  `).join('');

  slideListEl.querySelectorAll('.slide-item').forEach(el => {
    el.addEventListener('click', e => {
      if (e.target.closest('.slide-item__drag')) return;
      selectSlide(parseInt(el.dataset.id));
    });
  });

  if (window._sortable) window._sortable.destroy();
  window._sortable = new Sortable(slideListEl, {
    animation: 150,
    handle: '.slide-item__drag',
    ghostClass: 'sortable-ghost',
    onEnd: async () => {
      const ids = [...slideListEl.querySelectorAll('.slide-item')].map(el => parseInt(el.dataset.id));
      await api('/slides/reorder', { method: 'PATCH', body: JSON.stringify({ slide_ids: ids }) });
      await loadSlides();
      toast('Slides reordered');
    },
  });
}

// ── Select Slide ──
async function selectSlide(id) {
  currentSlideId = id;
  currentSlide = slides.find(s => s.id === id);
  if (!currentSlide) return;

  editorEmpty.style.display = 'none';
  editorContent.style.display = '';
  editType.value = currentSlide.slide_type;

  // Build fields from HTML
  renderFieldsFromHTML(currentSlide.body_html, currentSlide.slide_type);

  // Also populate HTML tab
  htmlEditor.value = currentSlide.body_html;

  // Highlight in list
  slideListEl.querySelectorAll('.slide-item').forEach(el => {
    el.classList.toggle('active', parseInt(el.dataset.id) === id);
  });

  schedulePreview();
}

// ── Field Extraction ──
function getPath(el, root) {
  const parts = [];
  let cur = el;
  while (cur && cur !== root) {
    const parent = cur.parentElement;
    if (!parent) break;
    const idx = Array.from(parent.children).indexOf(cur);
    parts.unshift(idx);
    cur = parent;
  }
  return parts;
}

function getByPath(root, path) {
  let el = root;
  for (const i of path) {
    if (!el || !el.children || !el.children[i]) return null;
    el = el.children[i];
  }
  return el;
}

function extractFields(bodyHtml) {
  const doc = new DOMParser().parseFromString('<div id="r">' + bodyHtml + '</div>', 'text/html');
  const root = doc.getElementById('r');
  const fields = [];
  const captured = new Set();

  for (const def of FIELD_DEFS) {
    const els = root.querySelectorAll(def.sel);
    let n = 0;
    for (const el of els) {
      if (captured.has(el)) continue;
      // Skip if ancestor already captured
      let skip = false;
      for (const c of captured) { if (c.contains(el) && c !== el) { skip = true; break; } }
      if (skip) continue;
      captured.add(el);
      n++;

      const path = getPath(el, root);
      let value, meta = null;

      if (def.special === 'dark-title') {
        const acc = el.querySelector('.accent');
        meta = { accent: acc ? acc.textContent.trim() : '' };
        value = el.textContent.trim();
      } else if (def.special === 'light-title') {
        const br = el.querySelector('.brand');
        meta = { brand: br ? br.textContent.trim() : '' };
        // Get text without brand prefix
        if (br) {
          const clone = el.cloneNode(true);
          clone.querySelector('.brand').remove();
          value = clone.textContent.trim();
        } else {
          value = el.textContent.trim();
        }
      } else {
        value = el.textContent.trim();
      }

      fields.push({
        path,
        label: els.length > 1 ? `${def.label} ${n}` : def.label,
        value,
        input: def.input,
        special: def.special || null,
        meta,
      });
    }
  }
  return fields;
}

// ── Render Fields Form ──
function renderFieldsFromHTML(bodyHtml, slideType) {
  const fields = extractFields(bodyHtml);
  let html = '';
  let lastGroup = '';

  // Group labels for sections
  const sectionMap = {
    'Badge': 'Header', 'Title': 'Header', 'Slide Title': 'Header',
    'Subtitle': 'Header', 'Tag': 'Header',
    'Heading': 'Content', 'Subheading': 'Content', 'Text': 'Content',
    'Bullet': 'Bullets', 'Phase': 'Timeline', 'Step Title': 'Steps',
    'Step Desc': 'Steps', 'Value': 'Stats', 'Label': 'Stats',
    'KPI Value': 'KPIs', 'KPI Label': 'KPIs',
    'Name': 'Team', 'Role': 'Team', 'Bio': 'Team',
    'Column': 'Table', 'Cell': 'Table',
    'Footnote': 'Footer', 'Country': 'Countries', 'Flag': 'Countries',
  };

  for (let i = 0; i < fields.length; i++) {
    const f = fields[i];
    const baseLabel = f.label.replace(/\s+\d+$/, '');
    const group = sectionMap[baseLabel] || 'Content';

    if (group !== lastGroup) {
      html += `<div class="field-section">${group}</div>`;
      lastGroup = group;
    }

    // Special: dark title with accent input
    if (f.special === 'dark-title') {
      html += `
        <div class="field-group">
          <label class="field-label">${esc(f.label)}</label>
          <input class="field-input field-input--lg" data-idx="${i}" value="${escAttr(f.value)}">
        </div>
        <div class="field-group">
          <label class="field-label">Accent Word (highlighted)</label>
          <input class="field-input" data-accent="${i}" value="${escAttr(f.meta?.accent || '')}">
        </div>`;
    }
    // Special: light title with brand toggle
    else if (f.special === 'light-title') {
      html += `
        <div class="field-group">
          <label class="field-label">${esc(f.label)}</label>
          <input class="field-input field-input--lg" data-idx="${i}" value="${escAttr(f.value)}">
        </div>
        <div class="checkbox-row">
          <input type="checkbox" data-brand="${i}" ${f.meta?.brand ? 'checked' : ''}>
          <span>Show "Nofar" brand prefix</span>
        </div>`;
    }
    // Normal field
    else if (f.input === 'textarea') {
      html += `
        <div class="field-group">
          <label class="field-label">${esc(f.label)}</label>
          <textarea class="field-input" data-idx="${i}" rows="2">${esc(f.value)}</textarea>
        </div>`;
    } else {
      html += `
        <div class="field-group">
          <label class="field-label">${esc(f.label)}</label>
          <input class="field-input" data-idx="${i}" value="${escAttr(f.value)}">
        </div>`;
    }
  }

  fieldsPanel.innerHTML = html;

  // Store fields for save
  fieldsPanel._fields = fields;
  fieldsPanel._originalHTML = bodyHtml;

  // Live preview on input
  fieldsPanel.querySelectorAll('.field-input').forEach(el => {
    el.addEventListener('input', () => schedulePreview());
  });
  fieldsPanel.querySelectorAll('[data-accent], [data-brand]').forEach(el => {
    el.addEventListener('input', () => schedulePreview());
    el.addEventListener('change', () => schedulePreview());
  });
}

// ── Collect form fields back into HTML ──
function collectFieldsToHTML() {
  if (activeTab === 'html') return htmlEditor.value;

  const fields = fieldsPanel._fields;
  const origHTML = fieldsPanel._originalHTML;
  if (!fields || !origHTML) return origHTML || '';

  // Re-parse original HTML
  const doc = new DOMParser().parseFromString('<div id="r">' + origHTML + '</div>', 'text/html');
  const root = doc.getElementById('r');

  for (let i = 0; i < fields.length; i++) {
    const f = fields[i];
    const el = getByPath(root, f.path);
    if (!el) continue;

    const input = fieldsPanel.querySelector(`[data-idx="${i}"]`);
    if (!input) continue;
    const newVal = input.value;

    if (f.special === 'dark-title') {
      const accentInput = fieldsPanel.querySelector(`[data-accent="${i}"]`);
      const accent = accentInput ? accentInput.value.trim() : '';
      if (accent && newVal.includes(accent)) {
        const idx = newVal.indexOf(accent);
        const before = newVal.substring(0, idx);
        const after = newVal.substring(idx + accent.length);
        el.innerHTML = esc(before) + '<span class="accent">' + esc(accent) + '</span>' + esc(after);
      } else {
        el.textContent = newVal;
      }
    } else if (f.special === 'light-title') {
      const brandCb = fieldsPanel.querySelector(`[data-brand="${i}"]`);
      const showBrand = brandCb ? brandCb.checked : false;
      if (showBrand) {
        el.innerHTML = '<span class="brand">Nofar</span> ' + esc(newVal);
      } else {
        el.textContent = newVal;
      }
    } else {
      el.textContent = newVal;
    }
  }

  return root.innerHTML;
}

// ── Add Content ──
function addTextBlock() {
  if (!currentSlide) return;
  // Switch to HTML tab, add a paragraph
  const html = collectFieldsToHTML();
  const newHTML = html + '\n<p>New text paragraph</p>';
  reloadEditor(newHTML);
  toast('Text block added');
}

function addBulletBlock() {
  if (!currentSlide) return;
  const html = collectFieldsToHTML();
  const newHTML = html + '\n<ul class="bullet-list">\n  <li>New bullet point</li>\n</ul>';
  reloadEditor(newHTML);
  toast('Bullet list added');
}

function reloadEditor(newHTML) {
  fieldsPanel._originalHTML = newHTML;
  renderFieldsFromHTML(newHTML, editType.value);
  htmlEditor.value = newHTML;
  schedulePreview();
}

// ── Save ──
async function saveSlide() {
  if (!currentSlideId) return;
  const bodyHtml = collectFieldsToHTML();

  // Extract title from the HTML for the slide list
  const doc = new DOMParser().parseFromString('<div>' + bodyHtml + '</div>', 'text/html');
  const h1 = doc.querySelector('h1');
  const h2 = doc.querySelector('h2');
  const title = (h1 || h2) ? (h1 || h2).textContent.trim() : currentSlide.title;

  await api(`/slides/${currentSlideId}`, {
    method: 'PUT',
    body: JSON.stringify({
      title,
      slide_type: editType.value,
      body_html: bodyHtml,
    }),
  });
  await loadSlides();
  // Re-select to refresh fields
  currentSlide = slides.find(s => s.id === currentSlideId);
  toast('Slide saved');
}

// ── Delete ──
async function deleteSlide() {
  if (!currentSlideId) return;
  if (!confirm('Delete this slide?')) return;
  await api(`/slides/${currentSlideId}`, { method: 'DELETE' });
  currentSlideId = null;
  currentSlide = null;
  editorEmpty.style.display = '';
  editorContent.style.display = 'none';
  previewFrame.src = 'about:blank';
  await loadSlides();
  toast('Slide deleted');
}

// ── Duplicate ──
async function duplicateSlide() {
  if (!currentSlideId) return;
  const s = await api(`/slides/${currentSlideId}/duplicate`, { method: 'POST' });
  await loadSlides();
  selectSlide(s.id);
  toast('Slide duplicated');
}

// ── Preview ──
let _previewTimer;
function schedulePreview() {
  clearTimeout(_previewTimer);
  _previewTimer = setTimeout(updatePreview, 300);
}

function updatePreview() {
  const slideType = editType.value;
  const bodyHtml = collectFieldsToHTML();
  const html = `<!DOCTYPE html>
<html><head>
<link rel="stylesheet" href="/static/presentation.css">
<style>
html, body { width: 100%; height: 100%; overflow: auto; }
.slide { position: relative; opacity: 1; visibility: visible; transform: none; min-height: 100%; }
</style>
</head><body>
<div class="slide slide--${slideType}">${bodyHtml}</div>
</body></html>`;

  const blob = new Blob([html], { type: 'text/html' });
  previewFrame.src = URL.createObjectURL(blob);
}

// ── Templates ──
async function loadTemplates() {
  templates = await api('/templates');
}

function openTemplateModal() {
  templateGrid.innerHTML = templates.map(t => `
    <div class="template-card" data-id="${t.id}">
      <div class="template-card__name">${esc(t.name)}</div>
      <div class="template-card__desc">${esc(t.description)}</div>
      <span class="template-card__type slide-item__type--${t.slide_type}">${t.slide_type}</span>
    </div>
  `).join('') + `
    <div class="template-card" data-id="blank-dark">
      <div class="template-card__name">Blank Dark</div>
      <div class="template-card__desc">Empty dark slide</div>
      <span class="template-card__type slide-item__type--dark">dark</span>
    </div>
    <div class="template-card" data-id="blank-light">
      <div class="template-card__name">Blank Light</div>
      <div class="template-card__desc">Empty light slide</div>
      <span class="template-card__type slide-item__type--light">light</span>
    </div>
  `;
  templateGrid.querySelectorAll('.template-card').forEach(el => {
    el.addEventListener('click', () => createFromTemplate(el.dataset.id));
  });
  modalTemplates.style.display = '';
}

async function createFromTemplate(tid) {
  modalTemplates.style.display = 'none';
  let data;
  if (tid === 'blank-dark') {
    data = { slide_type: 'dark', title: 'New Slide', body_html: '<div class="divider-badge">SECTION</div>\n<h1>New <span class="accent">Slide</span></h1>\n<p class="subtitle">Subtitle text</p>\n<div class="divider-line"></div>' };
  } else if (tid === 'blank-light') {
    data = { slide_type: 'light', title: 'New Slide', body_html: '<div class="slide-header">\n  <h2><span class="brand">Nofar</span> New Slide</h2>\n</div>\n<p>Add your content here.</p>' };
  } else {
    const t = templates.find(t => t.id === parseInt(tid));
    if (!t) return;
    data = { slide_type: t.slide_type, title: t.name, body_html: t.body_html };
  }
  const s = await api('/slides', { method: 'POST', body: JSON.stringify(data) });
  await loadSlides();
  selectSlide(s.id);
  toast('Slide created');
}

// ── Export ──
async function exportPresentation() {
  const res = await fetch('/presentation/export');
  const html = await res.text();
  const blob = new Blob([html], { type: 'text/html' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'nofar-presentation.html';
  a.click();
  toast('Exported');
}

// ── Utilities ──
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
function escAttr(s) {
  return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}
