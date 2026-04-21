"""
Daily Professional English Phrases Generator
Uses ZhipuAI (GLM) API to generate content and renders it into template.html

Requirements:
  pip install zhipuai

GitHub Secret needed:
  GLM_API_KEY  — your ZhipuAI API key from https://open.bigmodel.cn
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zhipuai import ZhipuAI

# ── Config ──────────────────────────────────────────────────────────────────

BEIJING = timezone(timedelta(hours=8))
now = datetime.now(BEIJING)

DATE_DISPLAY = now.strftime("%B %d, %Y")       # e.g. "April 22, 2026"
DATE_SLUG    = now.strftime("%Y-%m-%d")         # e.g. "2026-04-22"

MODEL = "glm-4.7-flash"   # or "glm-4-flash" for a cheaper/faster option

CATEGORY_LABELS = {
    "meeting language":        "Meetings",
    "email/report writing":    "Reports & Writing",
    "polite disagreement":     "Polite Disagreement",
    "presenting ideas":        "Presenting",
    "asking for clarification":"Clarification",
    "transitions & wrap-up":   "Transitions",
}

# ── Prompt ───────────────────────────────────────────────────────────────────

PROMPT = f"""You are a professional English coach for non-native speakers working in corporate environments.

Today is {DATE_DISPLAY}. Generate exactly 5 high-value professional English phrases.

Rotate the categories across the week — today pick a balanced mix from:
- meeting language
- email/report writing
- polite disagreement
- presenting ideas
- asking for clarification
- transitions & wrap-up

For each phrase return a JSON object with these exact keys:
- "phrase": the phrase itself (string)
- "category": one of the category names listed above (string, lowercase)
- "meaning": 1-2 sentences explaining what it means and when to use it (string)
- "example1": a realistic work-context sentence using the phrase (string, no surrounding quotes)
- "example2": another realistic work-context sentence (string, no surrounding quotes)
- "tip": one tone tip — e.g. formal vs informal register, when NOT to use it, or a common mistake to avoid (string)

Return ONLY a valid JSON array of 5 objects. No markdown fences, no explanation, no extra text."""

# ── Call GLM API ─────────────────────────────────────────────────────────────

client = ZhipuAI(api_key=os.environ["GLM_API_KEY"])

response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": PROMPT}],
    temperature=0.9,
)

raw = response.choices[0].message.content.strip()

# Strip markdown code fences if the model added them anyway
raw = re.sub(r"^```(?:json)?\s*", "", raw)
raw = re.sub(r"\s*```$", "", raw)

phrases = json.loads(raw)
assert len(phrases) == 5, f"Expected 5 phrases, got {len(phrases)}"

# ── Build phrase cards HTML ───────────────────────────────────────────────────

def build_cards(phrases):
    cards = ""
    for i, p in enumerate(phrases, 1):
        tag = CATEGORY_LABELS.get(p["category"].lower().strip(), p["category"])
        num = f"0{i}" if i < 10 else str(i)
        cards += f"""
    <div class="card" data-phrase="{i}">
      <div class="card-meta">
        <div class="card-number">{num}</div>
        <div class="card-tag">{tag}</div>
      </div>
      <div class="phrase">{p['phrase']}</div>
      <div class="meaning">{p['meaning']}</div>
      <div class="section-label">Examples</div>
      <div class="examples">
        <div class="example">"{p['example1']}"</div>
        <div class="example">"{p['example2']}"</div>
      </div>
      <div class="section-label">Tone Tip</div>
      <div class="tip">{p['tip']}</div>
    </div>"""
    return cards

# ── Build archive list HTML ───────────────────────────────────────────────────

def build_archive_list():
    """Scan the archive/ folder and build a list of all past days, newest first."""
    archive_dir = Path("archive")
    entries = ""

    if archive_dir.exists():
        files = sorted(archive_dir.glob("*.html"), reverse=True)
        for f in files:
            slug = f.stem                          # e.g. "2026-04-22"
            try:
                d = datetime.strptime(slug, "%Y-%m-%d")
                label = d.strftime("%B %d, %Y")
            except ValueError:
                continue

            is_today = slug == DATE_SLUG
            badge = '<span class="today-badge">Today</span>' if is_today else ""

            # Read first phrase name from archive file for preview
            content = f.read_text(encoding="utf-8")
            preview_phrases = re.findall(r'<div class="phrase">(.*?)</div>', content)
            preview = " · ".join(preview_phrases[:3]) + (" · …" if len(preview_phrases) > 3 else "")

            entries += f"""
    <a href="archive/{slug}.html" class="archive-item">
      <div class="archive-left">
        <div class="archive-date">{label} {badge}</div>
        <div class="archive-preview">{preview}</div>
      </div>
      <div class="archive-arrow">›</div>
    </a>"""

    if not entries:
        entries = '<p style="color:#aaa;font-size:14px;text-align:center;padding:40px 0;">No past entries yet.</p>'

    return entries

# ── Render & save ─────────────────────────────────────────────────────────────

template = Path("template.html").read_text(encoding="utf-8")

cards_html   = build_cards(phrases)
archive_html = build_archive_list()   # build before saving today's archive

# Save today as a standalone archive page (no archive list inside it)
archive_page = (template
    .replace("{{DATE}}", DATE_DISPLAY)
    .replace("{{CARDS}}", cards_html)
    .replace("{{ARCHIVE_LIST}}", archive_html))

Path("archive").mkdir(exist_ok=True)
Path(f"archive/{DATE_SLUG}.html").write_text(archive_page, encoding="utf-8")

# Rebuild archive list now that today's file exists
archive_html = build_archive_list()

# Save index.html (the main site)
index_page = (template
    .replace("{{DATE}}", DATE_DISPLAY)
    .replace("{{CARDS}}", cards_html)
    .replace("{{ARCHIVE_LIST}}", archive_html))

Path("index.html").write_text(index_page, encoding="utf-8")

print(f"✅ Generated phrases for {DATE_DISPLAY}")
print("Phrases:")
for i, p in enumerate(phrases, 1):
    print(f"  {i}. {p['phrase']}  [{p['category']}]")
