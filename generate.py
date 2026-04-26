"""
Daily Professional English Phrases Generator
Uses ZhipuAI (GLM) API via direct HTTP — no third-party packages needed.

GitHub Secret needed:
  GLM_API_KEY — your ZhipuAI API key from https://open.bigmodel.cn
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

BEIJING = timezone(timedelta(hours=8))
now = datetime.now(BEIJING)

DATE_DISPLAY = now.strftime("%B %d, %Y")       # e.g. "April 22, 2026"
DATE_SLUG    = now.strftime("%Y-%m-%d")         # e.g. "2026-04-22"

MODEL = "GLM-4-Flash-250414"

PHRASE_BANK_FILE = Path("phrases_used.json")    # tracks all phrases ever generated

CATEGORY_LABELS = {
    "meeting language":        "Meetings",
    "email/report writing":    "Reports & Writing",
    "polite disagreement":     "Polite Disagreement",
    "presenting ideas":        "Presenting",
    "asking for clarification":"Clarification",
    "transitions & wrap-up":   "Transitions",
}

# ── Load past phrases for deduplication ───────────────────────────────────

def load_past_phrases():
    if PHRASE_BANK_FILE.exists():
        try:
            data = json.loads(PHRASE_BANK_FILE.read_text(encoding="utf-8"))
            return [p.lower().strip() for p in data.get("phrases", [])]
        except (json.JSONDecodeError, KeyError):
            pass
    return []

# ── Build deduplication instruction ────────────────────────────────────────

def build_dedup_note(past_phrases):
    if not past_phrases:
        return (
            "IMPORTANT: No phrases have been generated before. "
            "Choose fresh, high-value expressions that are commonly useful in corporate settings."
        )
    # Show last 30 days of phrases (most relevant for avoiding recent repetition)
    recent = past_phrases[-30:]
    examples = ", ".join(f'"{p}"' for p in recent)
    return (
        f"AVOID repeating any of these phrases already used in recent days: "
        f"{examples}. "
        f"Do NOT use any phrase above or too-similar variations."
    )

# ── Build length instruction ───────────────────────────────────────────────

LENGTH_NOTE = (
    "MIX of LENGTHS required — exactly 3 short and 2 longer:\n"
    "  - Short (3): flexible CORE EXPRESSIONS, 2-6 words, embeddable in many sentences. "
    "Think: useful "chunks" or "atoms" people can drop into their own words. "
    "Examples: \"can't help doing\", \"circle back on\", \"parallel to this\", \"on the same page\", "
    "\"touch base\", \"per my last email\", \"just wanted to flag\", \"picking up on\", \"wrapping up\".\n"
    "  - Longer (2): semi-complete expressions, 8-15 words, still usable as stand-alone phrases. "
    "Examples: \"I see your point, but let's explore a different angle\", "
    "\"would you mind elaborating on that point\", "
    "\"to ensure we're aligned on next steps\"."
)

# ── Prompt ───────────────────────────────────────────────────────────────────

def build_prompt(date_display, past_phrases):
    dedup = build_dedup_note(past_phrases)

    return f"""You are a professional English coach for non-native speakers working in corporate environments.

Today is {date_display}. Generate exactly 5 high-value professional English phrases.

{dedup}

{LENGTH_NOTE}

Rotate the categories across the week — pick a balanced mix from:
- meeting language
- email/report writing
- polite disagreement
- presenting ideas
- asking for clarification
- transitions & wrap-up

For each phrase return a JSON object with these exact keys:
- "phrase": the core expression itself (string) — a flexible, stand-alone chunk that can be embedded naturally in many sentences. Keep it compact and memorable. NOT a full sentence with specific subject/object.
- "category": one of the category names listed above (string, lowercase)
- "meaning": 1-2 sentences explaining what it means and when to use it (string)
- "example1": a realistic work-context sentence using the phrase (string, no surrounding quotes)
- "example2": another realistic work-context sentence (string, no surrounding quotes)
- "tip": one tone tip — e.g. formal vs informal register, when NOT to use it, or a common mistake to avoid (string)

Return ONLY a valid JSON array of 5 objects. No markdown fences, no explanation, no extra text."""

# ── Call GLM API (pure stdlib, no pip installs needed) ───────────────────────

api_key = os.environ["GLM_API_KEY"]
past_phrases = load_past_phrases()
prompt = build_prompt(DATE_DISPLAY, past_phrases)

payload = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.9,
}).encode("utf-8")

req = urllib.request.Request(
    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    },
    method="POST",
)

with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read().decode("utf-8"))

raw = result["choices"][0]["message"]["content"].strip()

# Strip markdown code fences if the model added them anyway
raw = re.sub(r"^```(?:json)?\s*", "", raw)
raw = re.sub(r"\s*```$", "", raw)

phrases = json.loads(raw)
assert len(phrases) == 5, f"Expected 5 phrases, got {len(phrases)}"

# ── Update phrase bank ───────────────────────────────────────────────────────

phrase_bank = {"phrases": past_phrases}
for p in phrases:
    phrase_bank["phrases"].append(p["phrase"].lower().strip())
PHRASE_BANK_FILE.write_text(json.dumps(phrase_bank, ensure_ascii=False, indent=2), encoding="utf-8")

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
            slug = f.stem
            try:
                d = datetime.strptime(slug, "%Y-%m-%d")
                label = d.strftime("%B %d, %Y")
            except ValueError:
                continue

            is_today = slug == DATE_SLUG
            badge = '<span class="today-badge">Today</span>' if is_today else ""

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
archive_html = build_archive_list()

archive_page = (template
    .replace("{{DATE}}", DATE_DISPLAY)
    .replace("{{CARDS}}", cards_html)
    .replace("{{ARCHIVE_LIST}}", archive_html))

Path("archive").mkdir(exist_ok=True)
Path(f"archive/{DATE_SLUG}.html").write_text(archive_page, encoding="utf-8")

archive_html = build_archive_list()

index_page = (template
    .replace("{{DATE}}", DATE_DISPLAY)
    .replace("{{CARDS}}", cards_html)
    .replace("{{ARCHIVE_LIST}}", archive_html))

Path("index.html").write_text(index_page, encoding="utf-8")

print(f"✅ Generated phrases for {DATE_DISPLAY}")
print("Phrases:")
for i, p in enumerate(phrases, 1):
    print(f"  {i}. {p['phrase']}  [{p['category']}]")
