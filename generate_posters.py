"""
Generate L1-L15 GE posters: async API calls + threaded PNG rendering.
"""
import os, re, json, base64, openpyxl, asyncio
from concurrent.futures import ThreadPoolExecutor
from openai import AsyncOpenAI
from playwright.sync_api import sync_playwright

WORK_DIR = r"E:\51talk_automation\post_generator"
OUT_DIR = os.path.join(WORK_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

client = AsyncOpenAI(
    api_key="sk-UcHLM9G1fYCgefyghOfdMFJuCrA31Hhrc2uHGLTak4IjG03o",
    base_url="https://api.vectorengine.ai/v1",
)

with open(os.path.join(WORK_DIR, "51talklogo.png"), "rb") as f:
    LOGO_B64 = base64.b64encode(f.read()).decode()

STOPWORDS = {
    'the','a','an','is','are','am','was','were','be','been','being',
    'have','has','had','do','does','did','will','would','shall','should','can','could',
    'may','might','must','i','you','he','she','it','we','they','me','him','her','us','them',
    'my','your','his','its','our','their','this','that','these','those',
    'to','of','in','on','at','by','for','with','about','from','up','out','down','off',
    'and','but','or','so','because','if','when','then','not','no','yes','very','just',
    'here','there','too','all','some','any','each','every','one','two','go','get','got',
    'also','more','much','many','how','what','where','when','who','which','why',
    'don','doesn','isn','aren','wasn','weren','let','want','need','like','know',
    'really','well','right','left','say','said','come','came','take','took','make','made',
    'use','used','think','thing','things','way','day','time','today','now','see','look',
    'good','bad','big','small','new','old','back','still','even','only','first','please',
    'going','been','did','does','has','had','doing','bit','lot','kind','sort','ok','okay','s','t',
}

SPIRAL_NAMES = ["Core", "Details", "Polite", "Adapt", "Questions", "Review"]

def load_ge_pain_points():
    path = os.path.join(WORK_DIR, "_ge_marketing.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            rows = json.load(f)
        groups = []
        for row in rows:
            if not row or not row[0]: continue
            if str(row[0]).strip() == "Is this you?" and len(row) > 1 and row[1]:
                lines = [l.strip() for l in str(row[1]).split("\n") if l.strip()]
                question = next((l for l in lines if not l.startswith("❌")), "")
                bullets = [l for l in lines if l.startswith("❌")][:3]
                others = [l for l in lines if not l.startswith("❌") and l != question]
                cta = others[-1] if others else ""
                groups.append({"question": question, "bullets": bullets, "cta": cta})
        return groups
    except Exception as e:
        print(f"  Pain points load failed: {e}")
        return []

def validate_quotes(data, s):
    sentences = s.get("sentences", []) + s.get("expressions", [])
    all_text = " ".join(sentences).lower()
    for q in data.get("quotes", []):
        if not q or q == "null" or not q.strip(): continue
        q_key = q.strip('"').strip().lower()
        words = q_key.split()
        if len(words) >= 4 and " ".join(words[:4]) not in all_text:
            print(f"  QUOTE WARN L{s['level_num']}: '{q[:55]}' may be invented")
COURSE_NAME = "English for the Kingdom"

GE_CEFR = {
    1: ("A1 Low", "The Foundation", "Basic requests & introductions"),
    2: ("A1 High", "Daily Life", "Simple descriptions & routines"),
    3: ("A2 Low", "The Explorer", "Past events & future plans"),
    4: ("A2 Mid", "The Connector", "Reasons, directions & advice"),
    5: ("A2 High", "The Problem Solver", "Complaints, comparisons & health"),
    6: ("A2 Peak", "The Storyteller", "Narratives, conditions & culture"),
    7: ("B1 Low", "The Opinion Giver", "Preferences, relative clauses & recommendations"),
    8: ("B1 Mid", "The Experience Sharer", "Present perfect, modals & career talk"),
    9: ("B1 High", "The Critical Thinker", "Concession, emphasis & hypotheticals"),
    10: ("B2 Low", "The Debater", "Stance, evidence & rebuttal"),
    11: ("B2 Mid", "The Negotiator", "Passive voice, persuasion & money"),
    12: ("B2 High", "The Analyst", "Inversion, abstract topics & nuance"),
    13: ("C1 Low", "The Rhetorician", "Advanced idioms, implicit meaning & flexibility"),
    14: ("C1 Mid", "The Stylist", "Register switching, complex writing & abstract debate"),
    15: ("C1 High", "The Influencer", "Rhetorical devices, executive presence & identity"),
}

DIFFICULTY = {
    (1,3): "A1 BEGINNER. Sentences 3-8 words, present tense only. Basic daily vocab (food, family, places). NO past tense, modals, clauses, abstract words.",
    (4,6): "A2 ELEMENTARY. Sentences 8-15 words. Past/future OK, simple conjunctions (and/but/because). Travel, shopping, health vocab. NO present perfect, conditionals, passive voice.",
    (7,9): "B1 INTERMEDIATE. Sentences 15-25 words, complex sentences OK. Opinions, career, culture vocab. Present perfect, conditionals, relative clauses OK. NO subjunctive, inversion.",
    (10,12): "B2 UPPER-INTERMEDIATE. Complex sentences, abstract topics. Debate, negotiation, analysis vocab. Subjunctive, passive, indirect speech OK. NO C1 idioms or rhetorical devices.",
    (13,15): "C1 ADVANCED. Full complexity. Idioms, metaphors, rhetorical devices, register switching. Abstract, sophisticated vocabulary. Native-level nuance.",
}

# ─── Data Extraction ────────────────────────────────────────────────────────

def extract_level_stats():
    wb = openpyxl.load_workbook(os.path.join(WORK_DIR, "KSA GE Project Sheet 20260320.xlsx"), data_only=True)
    ws = wb["NEW Syllabus"]
    levels = {}
    current = None

    for row in ws.iter_rows(min_row=1, max_row=200, values_only=True):
        r0 = str(row[0]).strip() if row[0] else ""
        if r0.startswith("L") and len(r0) <= 3:
            current = r0
            levels[current] = {"units": [], "chunks": [], "core_vocab": set(), "core_sentences": [], "themes": []}
        elif current and r0.startswith("U") and r0 != "Unit":
            up = str(row[5]) if len(row) > 5 and row[5] else ""
            cr = str(row[3]) if len(row) > 3 and row[3] else ""
            theme = str(row[1])[:120] if len(row) > 1 and row[1] else ""
            m = re.search(r'Vocab:\s*(.+?)(?:\||$)', up)
            if m:
                for v in m.group(1).split(","):
                    v = v.strip()
                    if v and len(v) > 1: levels[current]["core_vocab"].add(v)
            m = re.search(r'Sentence:\s*[「"“]?(.+?)[」"”]?(?:\||$)', up)
            if m:
                s = m.group(1).strip().strip('"').strip('“').strip('”')
                if s: levels[current]["core_sentences"].append(s)
            for line in cr.split("\n"):
                line = line.strip().strip('"')
                if line and len(line) > 5 and not line.startswith("Key Functional"):
                    levels[current]["chunks"].append(line[:150])
            levels[current]["themes"].append(theme)
            levels[current]["units"].append({"theme": theme, "task": str(row[2])[:200] if len(row) > 2 and row[2] else ""})

    for lnum in range(1, 16):
        sn = f"L{lnum}"
        if sn not in wb.sheetnames or sn not in levels: continue
        ws2 = wb[sn]
        lvl = levels[sn]
        lesson_count = 0
        lesson_words = set()
        golden_sentences = []
        for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, values_only=True):
            if not row[0] or not str(row[0]).strip().isdigit(): continue
            if not row[1] or not str(row[1]).strip().isdigit(): continue
            lesson_count += 1
            combined = ""
            for c in row[2:6]:
                if c: combined += str(c) + "\n"
            m = re.search(r'Target Vocab:\s*(.+?)(?:\n|\Z)', combined)
            if m:
                for v in m.group(1).split(","):
                    v = v.strip().lower()
                    if v and len(v) > 1 and v not in STOPWORDS: lesson_words.add(v)
            m = re.search(r'Golden Sentence:\s*"?(.+?)"?(?:\n|\Z)', combined)
            if m:
                s = m.group(1).strip().strip('"').strip()
                if s and len(s) > 5: golden_sentences.append(s[:150])
        lvl["lesson_count"] = lesson_count
        lvl["lesson_words"] = lesson_words
        lvl["golden_sentences"] = golden_sentences

    for sn in levels:
        expr_words = set()
        for e in set(levels[sn]["chunks"]):
            for w in re.findall(r'[a-zA-Z]+', e.lower()):
                if w not in STOPWORDS and len(w) > 2: expr_words.add(w)
        levels[sn]["expr_words"] = expr_words
        for s in levels[sn].get("golden_sentences", []):
            s_clean = s.strip().strip('"').strip()
            if s_clean and len(s_clean) > 5: levels[sn]["chunks"].append(s_clean[:150])

    stats = {}
    for sn in sorted(levels.keys(), key=lambda x: int(x[1:])):
        l = levels[sn]
        lv = int(sn[1:])
        unique_chunks = list(dict.fromkeys(l["chunks"]))
        combined_vocab = set(l.get("lesson_words", set()))
        combined_vocab.update(v.lower() for v in l["core_vocab"])
        combined_vocab.update(l.get("expr_words", set()))
        stat_mode = "words" if lv <= 6 else "patterns"
        stats[sn] = {
            "level_num": lv, "unit_count": len(l["units"]),
            "lesson_count": l.get("lesson_count", len(l["units"]) * 6),
            "total_vocab_count": len(combined_vocab),
            "core_vocab_sample": sorted(combined_vocab)[:20],
            "expression_count": len(unique_chunks),
            "expressions": unique_chunks[:8],
            "sentences": list(dict.fromkeys(l["core_sentences"]))[:5],
            "themes": l["themes"][:8], "stat_mode": stat_mode,
        }
    wb.close()
    return stats

# ─── Prompt & API ───────────────────────────────────────────────────────────

def build_prompt(s, cefr):
    sn = f"L{s['level_num']}"
    cefr_band, persona, focus = cefr
    lv = s["level_num"]
    diff = next(v for (lo, hi), v in DIFFICULTY.items() if lo <= lv <= hi)
    sentences = "\n".join([f'  "{x}"' for x in s["sentences"][:4]])
    exprs = "\n".join([f'  "{x}"' for x in s["expressions"][:5]])
    themes = "\n".join([f"  - {x}" for x in s["themes"]])
    vocab_sample = ", ".join(s["core_vocab_sample"][:15])
    stat_desc = (
        f"{s['total_vocab_count']} new words, {s['expression_count']} expressions — lead with vocabulary"
        if s["stat_mode"] == "words" else
        f"{s['expression_count']} advanced functional patterns containing {s['total_vocab_count']}+ vocabulary items — lead with patterns"
    )

    return f"""You fill content into a fixed English course poster. Output ONLY a JSON object. No markdown, no explanation.

## Course: {COURSE_NAME}
## Level: {sn} / {cefr_band} / {persona} — "{focus}"
- {s['lesson_count']} live 25-min sessions, {s['unit_count']} real-life scenarios x 6 layers each
- {stat_desc}
- Students produce their OWN sentences every lesson

## LANGUAGE LEVEL (CRITICAL)
{diff}
ALL content in the JSON MUST match this level. Sentences at low levels must be SHORT and SIMPLE.

## Real Syllabus Data (use these — don't invent)

Sentences students will say:
{sentences if sentences else exprs[:4]}

KSA scenarios:
{themes}

Sample vocabulary: {vocab_sample}

Spiral layers (fixed): {", ".join(SPIRAL_NAMES)}

## Output this JSON (fill ALL values):

```json
{{
  "hero_line": "ONE bold aspirational one-liner. Max 12 words. A PROMISE, not a description.",
  "hero_sub": "Supporting phrase, 5-8 words",
  "spiral_scenario": "ONE real scenario name from the syllabus above",
  "spiral_examples": [
    "Step 1 — simplest form, 3-5 words for low levels",
    "Step 2 — add detail, 5-8 words",
    "Step 3 — polite version, 6-10 words",
    "Step 4 — with adaptation, 6-12 words",
    "Step 5 — question form, 5-10 words",
    "Step 6 — full natural sentence combining everything, 8-18 words"
  ],
  "quotes": [
    "Real sentence 1 from syllabus",
    "Real sentence 2 from syllabus",
    "Real sentence 3 from syllabus (or null if only 2)"
  ],
  "scenario_tags": [
    "Scenario with emoji 1", "Scenario with emoji 2", "Scenario with emoji 3", "Scenario with emoji 4", "Scenario with emoji 5"
  ],
  "progress_text": "L{lv} of 15. Next: one-line promise about next level",
  "footer_cta": "Bold CTA, 6-10 words",
  "footer_tagline": "Supporting tagline, 5-10 words"
}}
```

RULES:
- hero_line: EMOTIONAL. ASPIRATIONAL. A promise.
- spiral_examples: SAME scenario across ALL 6 steps. Match {cefr_band} difficulty EXACTLY.
- quotes: Use REAL sentences from the syllabus data above. Do NOT invent new ones.
- scenario_tags: From syllabus themes above. Use real KSA names (Barn's, Careem, Boulevard World, Jarir, etc.).
- progress_text: What the student unlocks at the NEXT level.
- footer: Punchy, emotional, memorable.

Output JSON now:"""

async def call_api(s, cefr):
    sn = f"L{s['level_num']}"
    prompt = build_prompt(s, cefr)
    try:
        resp = await client.chat.completions.create(
            model="gemini-3.5-flash",
            messages=[
                {"role": "system", "content": "You are an education copywriter. Output valid JSON only. No markdown fences. Start with { and end with }."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7, max_tokens=4096,
        )
        raw = resp.choices[0].message.content.strip()
        for pfx in ["```json", "```JSON", "```"]:
            if raw.startswith(pfx): raw = raw[len(pfx):]
        if raw.endswith("```"): raw = raw[:-3]
        data = json.loads(raw.strip())
        for f in ["hero_line","hero_sub","spiral_scenario","spiral_examples","quotes","scenario_tags","progress_text","footer_cta","footer_tagline"]:
            if f not in data: print(f"  [{sn}] MISSING:{f}"); return None
        assert len(data["spiral_examples"]) == 6, f"[{sn}] Need 6 spiral examples"
        validate_quotes(data, s)
        print(f"  [{sn}] API OK")
        return {"sn": sn, "data": data, "stats": s, "cefr": cefr}
    except Exception as e:
        print(f"  [{sn}] API ERR: {e}")
        return None

# ─── HTML & PNG ─────────────────────────────────────────────────────────────

def fill_template(sn, data, s, cefr_band, pain_groups=None):
    with open(os.path.join(WORK_DIR, "poster_template.html"), "r", encoding="utf-8") as f:
        html = f.read()

    lv = s["level_num"]

    spiral_html = ""
    for i, (name, ex) in enumerate(zip(SPIRAL_NAMES, data["spiral_examples"])):
        spiral_html += f'<div class="spiral-step"><div class="step-num">{i+1}</div><div class="step-title">{name}</div><div class="step-example">"{ex}"</div></div>'
        if i < 5: spiral_html += '<div class="spiral-arrow">→</div>'

    quotes_html = "".join(f'<div class="quote">"{q}"</div>\n' for q in data["quotes"] if q and q != "null" and q.strip())
    tags_html = "".join(f'<span class="scenario-tag">{t}</span>\n' for t in data["scenario_tags"])
    dots_html = "".join(f'<div class="progress-dot {"filled" if i <= lv else ""}"></div>' for i in range(1, 16))

    group_idx = min((lv - 1) // 3, 4)
    if pain_groups and group_idx < len(pain_groups):
        pg = pain_groups[group_idx]
        items_html = "".join(f'<div class="pain-item">{b}</div>' for b in pg["bullets"])
        ity_html = f'<div class="pain-points"><div class="pain-q">{pg["question"]}</div>{items_html}<div class="pain-cta">{pg["cta"]}</div></div>'
    else:
        ity_html = ""

    milestones_map = {3: "A1", 6: "A2", 9: "B1", 12: "B2", 15: "C1"}
    ms_html = "".join(
        f'<div class="milestone{"" if i > lv else " hit"}">{milestones_map.get(i, "")}</div>'
        for i in range(1, 16)
    )

    html = html.replace("{{COURSE_NAME}}", COURSE_NAME)
    html = html.replace("{{LEVEL}}", sn)
    html = html.replace("{{CEFR}}", cefr_band)
    html = html.replace("{{HERO_LINE}}", data["hero_line"])
    html = html.replace("{{HERO_SUB}}", data["hero_sub"])
    html = html.replace("{{VOCAB_COUNT}}", str(s["total_vocab_count"]))
    html = html.replace("{{EXPR_COUNT}}", str(s["expression_count"]))
    html = html.replace("{{LESSON_COUNT}}", str(s["lesson_count"]))
    html = html.replace("{{SCENARIO_COUNT}}", str(s["unit_count"]))
    html = html.replace("{{EXAMPLE_SCENARIO}}", data["spiral_scenario"])
    html = html.replace("{{SPIRAL_STEPS}}", spiral_html)
    html = html.replace("{{QUOTES}}", quotes_html)
    html = html.replace("{{SCENARIO_TAGS}}", tags_html)
    html = html.replace("{{PROGRESS_DOTS}}", dots_html)
    html = html.replace("{{PROGRESS_MILESTONES}}", ms_html)
    html = html.replace("{{PROGRESS_TEXT}}", data["progress_text"])
    html = html.replace("{{WORD_LABEL}}", "New Words")
    html = html.replace("{{IS_THIS_YOU}}", ity_html)
    html = html.replace("{{FOOTER_CTA}}", data["footer_cta"])
    html = html.replace("{{FOOTER_TAGLINE}}", data["footer_tagline"])
    html = html.replace("__LOGO_B64__", f"data:image/png;base64,{LOGO_B64}")
    return html

def render_png(html_path, png_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 750, "height": 800}, device_scale_factor=4)
        page.goto(f"file:///{html_path.replace(chr(92), '/')}")
        page.wait_for_timeout(2000)
        height = page.evaluate("document.querySelector('.poster').getBoundingClientRect().bottom")
        page.set_viewport_size({"width": 750, "height": int(height) + 20})
        page.screenshot(path=png_path, full_page=True)
        browser.close()

# ─── Main ───────────────────────────────────────────────────────────────────

async def main():
    print("Extracting...")
    stats = extract_level_stats()
    pain_groups = load_ge_pain_points()
    print(f"  Pain point groups loaded: {len(pain_groups)}")
    cefr = GE_CEFR
    items = [(sn, stats[sn], cefr[stats[sn]["level_num"]]) for sn in sorted(stats.keys(), key=lambda x: int(x[1:]))]
    for sn, s, c in items:
        print(f"  {sn}: {s['lesson_count']}L, {s['total_vocab_count']}w+, {s['expression_count']}e")

    # Phase 1: All API calls in parallel
    print(f"\n=== Phase 1: {len(items)} API calls in parallel ===")
    results = await asyncio.gather(*[call_api(s, c) for _, s, c in items])
    results = [r for r in results if r is not None]
    print(f"  {len(results)}/{len(items)} API calls succeeded")

    # Phase 2: Fill templates
    print(f"\n=== Phase 2: Fill templates ===")
    html_files = []
    for r in results:
        sn, data, s, (cefr_band, _, _) = r["sn"], r["data"], r["stats"], r["cefr"]
        html = fill_template(sn, data, s, cefr_band, pain_groups)
        hf = os.path.join(OUT_DIR, f"GE_{sn}_poster.html")
        with open(hf, "w", encoding="utf-8") as f: f.write(html)
        html_files.append((sn, hf))
        print(f"  [{sn}] HTML saved")

    # Phase 3: All PNG renders in thread pool (Playwright is sync)
    print(f"\n=== Phase 3: {len(html_files)} PNG renders in parallel ===")
    def render_one(sn, hf):
        pf = os.path.join(OUT_DIR, f"GE_{sn}_poster.png")
        try:
            render_png(hf, pf)
            return (sn, pf, os.path.getsize(pf))
        except Exception as e:
            return (sn, None, str(e))

    with ThreadPoolExecutor(max_workers=4) as pool:
        png_results = list(pool.map(lambda x: render_one(*x), html_files))

    for sn, pf, sz in png_results:
        if pf:
            print(f"  [{sn}] PNG {sz:,} bytes")
        else:
            print(f"  [{sn}] PNG FAILED: {sz}")

    print(f"\nDone. Output: {OUT_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
