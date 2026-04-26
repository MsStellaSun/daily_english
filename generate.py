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

DATE_DISPLAY = now.strftime("%B %d, %Y")
DATE_SLUG    = now.strftime("%Y-%m-%d")

MODEL = "GLM-4-Flash-250414"

PHRASE_BANK_FILE = Path("phrases_used.json")

CATEGORY_LABELS = {
    "meeting language":        "Meetings",
    "email/report writing":    "Reports & Writing",
    "polite disagreement":     "Polite Disagreement",
    "presenting ideas":        "Presenting",
    "asking for clarification":"Clarification",
    "transitions & wrap-up":   "Transitions",
}

# ── Load past phrases ─────────────────────────────────────────────────────────

def load_past_phrases():
    if PHRASE_BANK_FILE.exists():
        try:
            data = json.loads(PHRASE_BANK_FILE.read_text(encoding="utf-8"))
            return [p.lower().strip() for p in data.get("phrases", [])]
        except (json.JSONDecodeError, KeyError):
            pass
    return []

# ── Build prompt: ask for 10 candidates, we pick 5 ──────────────────────────

def build_prompt(date_display, past_phrases):
    dedup = ""
    if past_phrases:
        recent = past_phrases[-30:]
        dedup = "Avoid repeating these: " + ", ".join(f'"{p}"' for p in recent) + ".\n"

    return f"""Generate exactly 10 candidate English phrases for professional corporate communication.

Today: {date_display}.
{dedup}

Generate a mix of:
- SHORT fragments (1-5 words): idiomatic chunks, verb phrases, prepositional phrases. Examples: "can't help wondering", "circle back on", "on the same page", "moving the needle", "touch base", "per my last email", "just wanted to flag", "picking up on", "wrapping up", "going forward"
- LONGER phrases (6-15 words): more complete expressions with some context. Examples: "I see your point, but let's explore a different angle", "would you mind elaborating on that point"

Return a JSON object (not array): {{"candidates": [{{"phrase": "...", "category": "...", "meaning": "...", "example1": "...", "example2": "...", "tip": "..."}}]}}
Return ONLY this JSON. No markdown fences. No explanation."""

# ── Pick best 5 from candidates ───────────────────────────────────────────────

def pick_best(candidates):
    chosen = []

    # First pick 3 shortest (1-5 words, prefer fragments without subject)
    short = [c for c in candidates if 1 <= len(c["phrase"].split()) <= 5]
    # Prefer phrases without subject pronouns at start
    short.sort(key=lambda c: (
        0 if re.match(r"^(i|you|we|they|it|he|she|this|that)", c["phrase"].lower().split()[0]) else 1,
        len(c["phrase"].split())
    ))
    chosen.extend(short[:3])

    # Then pick 2 medium (6-12 words)
    long_list = [c for c in candidates if 6 <= len(c["phrase"].split()) <= 12]
    long_list.sort(key=lambda c: len(c["phrase"].split()))
    chosen.extend(long_list[:2])

    # If we don't have enough, fill from remaining
    if len(chosen) < 5:
        remaining = [c for c in candidates if c not in chosen]
        chosen.extend(remaining[:5-len(chosen)])

    return chosen[:5]

# ── Call GLM API ─────────────────────────────────────────────────────────────

api_key = os.environ["GLM_API_KEY"]
past_phrases = load_past_phrases()
prompt = build_prompt(DATE_DISPLAY, past_phrases)

payload = json.dumps({
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.5,
    "max_tokens": 2500,
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

raw = re.sub(r"^```(?:json)?\s*", "", raw)
raw = re.sub(r"\s*```$", "", raw)

try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    print(f"Raw output:\n{raw}")
    raise

candidates = data.get("candidates", [])
# Handle if model returned array directly
if isinstance(data, list):
    candidates = data

print(f"Generated {len(candidates)} candidates")
for c in candidates:
    wc = len(c["phrase"].split())
    print(f"  [{wc}w] {c['phrase']}")

phrases = pick_best(candidates)
print(f"\nSelected {len(phrases)} phrases:")
for i, p in enumerate(phrases, 1):
    print(f"  {i}. [{len(p['phrase'].split())}w] {p['phrase']}")

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

print(f"\nGenerated for {DATE_DISPLAY}")
