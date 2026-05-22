"""
Generate L1-L15 BE posters: async API calls + threaded PNG rendering.
"""
import os, re, json, base64, openpyxl, asyncio
from concurrent.futures import ThreadPoolExecutor
from openai import AsyncOpenAI
from playwright.sync_api import sync_playwright

WORK_DIR = r"E:\51talk_automation\post_generator"
OUT_DIR = os.path.join(WORK_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

API_KEY = os.environ.get("LLM_API_KEY", "")
if not API_KEY:
    raise RuntimeError("LLM_API_KEY not set")

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=os.environ.get("LLM_BASE_URL", "https://api.vectorengine.ai/v1"),
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

SPIRAL_NAMES = ["Core", "Details", "Formal", "Adapt", "Questions", "Review"]

BE_HERO_SUB = {
    1:  "The Foundation — your first professional sentences",
    2:  "Routines & Descriptions — own your daily vocabulary",
    3:  "Interaction & Movement — navigate and take action",
    4:  "Experiences & Comparisons — tell your career story",
    5:  "Obligations & Processes — handle rules and instructions",
    6:  "Reasons & Explanations — explain yourself confidently",
    7:  "Coherence & Experience — flow through any conversation",
    8:  "Processes & Possibilities — manage complexity at work",
    9:  "Abstract Ideas & Future — lead with language",
    10: "Nuance & Indirectness — master the unspoken",
    11: "Persuasion & Complexity — influence every room",
    12: "Abstract Analysis & Style — command every register",
    13: "Implicit Meaning & Idiomatic Fluency — say more, mean more",
    14: "Stylistic Flexibility & Writing — write and speak with authority",
    15: "Rhetoric & Executive Presence — command the room",
}

SPIRAL_PHASES = [
    ("Build",  "#dbeafe", "#1d4ed8"),   # blue  — input & structure
    ("Apply",  "#dcfce7", "#166534"),   # green — speaking practice
    ("Master", "#fef9c3", "#854d0e"),   # gold  — expand & review
]

BE_PAIN_POINTS = {
    1: {
        "question": "Do you freeze up the moment a foreign colleague speaks?",
        "bullets": ["❌ Can't introduce yourself beyond \"My name is...\"?", "❌ Smile and nod — but understand nothing?", "❌ Avoid eye contact because you fear being asked anything?"],
        "cta": "Stop freezing. Start introducing.",
    },
    2: {
        "question": "Can you say words — but not your workday?",
        "bullets": ["❌ Can't explain your daily schedule in English?", "❌ Know the clock but can't say when your meeting is?", "❌ Describe your job title — but nothing else?"],
        "cta": "Stop surviving. Start describing.",
    },
    3: {
        "question": "Are you lost the moment someone asks what you're doing?",
        "bullets": ["❌ Can't say what you're working on right now?", "❌ Freeze up giving directions inside the office?", "❌ Go quiet on business trips the moment English starts?"],
        "cta": "Stop pointing. Start navigating.",
    },
    4: {
        "question": "Can you handle today — but not yesterday or tomorrow?",
        "bullets": ["❌ Can't talk about your work history in English?", "❌ Describe products — but can't compare them?", "❌ Struggle to explain what went wrong on a project?"],
        "cta": "Stop living in the present. Start telling your story.",
    },
    5: {
        "question": "Do rules and instructions trip you up every time?",
        "bullets": ["❌ Can't explain company policy to a foreign colleague?", "❌ Give instructions — but they always do it wrong?", "❌ Too polite to make a direct request in English?"],
        "cta": "Stop hinting. Start instructing.",
    },
    6: {
        "question": "Can you say what — but never why?",
        "bullets": ["❌ Can't explain your reasons in a job interview?", "❌ Know the answer — but can't justify it in English?", "❌ Emails land flat because you can't explain your logic?"],
        "cta": "Stop stating. Start explaining.",
    },
    7: {
        "question": "Can you speak — but not hold a conversation?",
        "bullets": ["❌ Lose the thread the moment topics get complex?", "❌ Can't tell your career story without rehearsing it first?", "❌ Small talk dies after \"I'm fine, thank you\"?"],
        "cta": "Stop answering. Start connecting.",
    },
    8: {
        "question": "Can you work the process — but not describe it?",
        "bullets": ["❌ Can't walk a foreign colleague through a workflow?", "❌ Struggle to explain company rules without sounding stiff?", "❌ Interviews go well — until they ask about problem-solving?"],
        "cta": "Stop doing. Start explaining.",
    },
    9: {
        "question": "Do big ideas shrink the moment you say them in English?",
        "bullets": ["❌ Can't present a Vision 2030 initiative without notes?", "❌ Define roles — but lose the bigger picture in English?", "❌ Predictions sound like guesses instead of leadership?"],
        "cta": "Stop shrinking. Start leading.",
    },
    10: {
        "question": "Is your English clear — but never subtle?",
        "bullets": ["❌ Say exactly what you mean — even when you shouldn't?", "❌ Miss the diplomatic layer in high-stakes meetings?", "❌ Give feedback that lands harder than you intended?"],
        "cta": "Stop being blunt. Start being strategic.",
    },
    11: {
        "question": "Can you argue — but never persuade?",
        "bullets": ["❌ Make your case — but no one changes their mind?", "❌ Crisis hits and your English becomes robotic?", "❌ Lead meetings — but lose control the moment it gets complex?"],
        "cta": "Stop arguing. Start influencing.",
    },
    12: {
        "question": "Is your English strong — but still not executive?",
        "bullets": ["❌ Formal emails sound stiff instead of authoritative?", "❌ Can't use emphasis without sounding aggressive?", "❌ Switch between spoken and written English awkwardly?"],
        "cta": "Stop writing. Start commanding.",
    },
    13: {
        "question": "Do you hear every word — but miss what's really being said?",
        "bullets": ["❌ Idioms land — but you laugh half a second too late?", "❌ Read the email — but can't read between the lines?", "❌ Miss the power dynamics in executive conversations?"],
        "cta": "Stop listening. Start reading the room.",
    },
    14: {
        "question": "Is your voice strong — but your writing still junior?",
        "bullets": ["❌ Proposals reviewed — but never approved as written?", "❌ Crisis statement drafted — but it sounds like an apology?", "❌ Shift register between emails and meetings awkwardly?"],
        "cta": "Stop drafting. Start publishing.",
    },
    15: {
        "question": "Are you the expert in the room — but not the voice?",
        "bullets": ["❌ Persuade individuals — but not entire rooms?", "❌ Abstract ideas lose precision the moment you speak?", "❌ Hostile questions throw you off instead of elevating you?"],
        "cta": "Stop being heard. Start being remembered.",
    },
}

def validate_quotes(data, s):
    pool = list(dict.fromkeys(s.get("sentences", []) + s.get("expressions", [])))
    all_text = " ".join(pool).lower()
    used = set()
    fixed = []
    for q in data.get("quotes", []):
        if not q or q == "null" or not q.strip():
            fixed.append(q)
            continue
        q_key = q.strip('"').strip().lower()
        words = q_key.split()
        if len(words) >= 4 and " ".join(words[:4]) not in all_text:
            replacement = next((r for r in pool if r not in used), None)
            if replacement:
                print(f"  QUOTE FIX L{s['level_num']}: '{q[:45]}' -> syllabus sentence")
                used.add(replacement)
                fixed.append(replacement)
            else:
                print(f"  QUOTE WARN L{s['level_num']}: no replacement for '{q[:45]}'")
                fixed.append(q)
        else:
            used.add(q.strip('"').strip())
            fixed.append(q)
    return fixed
COURSE_NAME = "Gateway to Vision 2030"

GE_CEFR = {
    1: ("A1 Low", "The Starter", "Greetings, jobs & introductions"),
    2: ("A1 High", "The Operator", "Routines, time & locations"),
    3: ("A1 Peak", "The Mover", "Directions, travel & current actions"),
    4: ("A2 Low", "The Reporter", "Work history, products & comparisons"),
    5: ("A2 Mid", "The Coordinator", "Rules, instructions & requests"),
    6: ("A2 High", "The Communicator", "Reasons, experience & interviews"),
    7: ("B1 Low", "The Professional", "Career path, meetings & opinions"),
    8: ("B1 Mid", "The Specialist", "Processes, policies & problem solving"),
    9: ("B1 High", "The Innovator", "Roles, creativity & reporting"),
    10: ("B2 Low", "The Diplomat", "Diplomacy, meetings & speculation"),
    11: ("B2 Mid", "The Negotiator", "Negotiation, crisis & projects"),
    12: ("B2 High", "The Analyst", "Formal writing, emphasis & abstract analysis"),
    13: ("C1 Low", "The Strategist", "Implicit meaning, idioms & nuanced opinions"),
    14: ("C1 Mid", "The Executive Writer", "Register, proposals & crisis communication"),
    15: ("C1 High", "The Visionary", "Persuasion, leadership & abstract concepts"),
}

DIFFICULTY = {
    (1,3): "A1 BEGINNER. Simple sentences, basic business vocab. NO past tense, modals, clauses.",
    (4,6): "A2 ELEMENTARY. Simple conjunctions. Travel, shopping, work vocab. NO perfect tenses, conditionals, passive.",
    (7,9): "B1 INTERMEDIATE. Complex sentences. Career, process vocab. Perfect tenses, conditionals, relative clauses OK.",
    (10,12): "B2 UPPER-INTERMEDIATE. Abstract topics. Subjunctive, passive, indirect speech OK.",
    (13,15): "C1 ADVANCED. Full complexity. Idioms, rhetoric, executive presence.",
}

def _parse_vocab(raw):
    """Split a vocab field value into individual clean words."""
    words = set()
    for item in raw.rstrip('.,').split(','):
        word = item.strip().strip("'\"").split('(')[0].strip().lower()
        if word and len(word) > 1 and word not in STOPWORDS:
            words.add(word)
    return words

def extract_be_stats():
    xlsx_path = os.path.join(os.path.dirname(WORK_DIR), "report_generator", "KSA BE 20260324.xlsx")
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    stats = {}

    for lnum in range(1, 16):
        sn = f"L{lnum}"
        if sn not in wb.sheetnames:
            continue
        ws = wb[sn]

        all_vocab = set()
        all_sentences = []
        themes = []
        seen_units = set()

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
            if not row[0] or not str(row[0]).strip().isdigit():
                continue
            content = str(row[2]) if row[2] else ""

            # Normalize L10-L12 format: {{"..<br>.."}} → plain \n-delimited text
            content = re.sub(r'^\{\{"?|"?\}\}$', '', content.strip())
            content = content.replace("<br>", "\n")

            unit_num = str(row[0]).strip()

            # Unit theme — covers all 3 format variants
            m = re.search(r'(?:Unit Info:|Unit:)\s*(?:Unit\s+)?\d+\s*[-–]\s*(.+?)(?:\n|$)', content)
            if m and unit_num not in seen_units:
                themes.append(m.group(1).strip())
                seen_units.add(unit_num)

            # Vocabulary
            for pat in [
                r'Core Vocab(?:ulary)?:\s*(.+?)(?:\n|$)',
                r'Power Words:\s*(.+?)(?:\n|$)',
                r'Strategic Vocab(?:ulary)?(?:\s*\([^)]*\))?:\s*(.+?)(?:\n|$)',
            ]:
                m = re.search(pat, content)
                if m:
                    all_vocab.update(_parse_vocab(m.group(1)))

            # Sentences — The Golden Sentence (L1-L9), GS (L10-L12), Visionary Statement (L13-L15)
            # Leading bullet/arrow may be any Unicode character, so match .* before label
            for pat in [
                r'The Golden Sentence:\s*(.+?)(?:\n|$)',
                r'GS:\s*(.+?)(?:\n|$)',
                r'Visionary Stat\w*(?:\s*\([^)]*\))?:\s*(.+?)(?:\n|$)',
                r'Core Structure(?:\s*/[^:]+)?:\s*(.+?)(?:\n|$)',
            ]:
                m = re.search(pat, content)
                if m:
                    for part in m.group(1).split('/'):
                        s = part.strip().strip('"').strip()
                        if s and len(s) > 5:
                            all_sentences.append(s[:150])

        unique_s = list(dict.fromkeys(all_sentences))
        unit_count = len(seen_units)
        stats[sn] = {
            "level_num": lnum,
            "unit_count": unit_count,
            "lesson_count": unit_count * 6,
            "total_vocab_count": len(all_vocab),
            "core_vocab_sample": sorted(all_vocab)[:20],
            "expression_count": len(unique_s),
            "expressions": unique_s[:8],
            "sentences": unique_s[:5],
            "themes": themes[:8],
        }

    wb.close()
    return stats

def build_prompt(s, cefr):
    sn = f"L{s['level_num']}"
    cefr_band, persona, focus = cefr
    lv = s["level_num"]
    diff = next(v for (lo, hi), v in DIFFICULTY.items() if lo <= lv <= hi)
    sentences = "\n".join([f'  "{x}"' for x in s["sentences"][:4]])
    themes = "\n".join([f"  - {x}" for x in s["themes"]])
    vocab_sample = ", ".join(s["core_vocab_sample"][:15])

    return f"""You fill content into a BUSINESS English course poster. Output ONLY a JSON object. No markdown, no explanation.

## Course: {COURSE_NAME} — Business English for Saudi professionals
## Level: {sn} / {cefr_band} / {persona} — "{focus}"
- {s['lesson_count']} live 25-min sessions, {s['unit_count']} business scenarios x 6 layers each
- {s['total_vocab_count']}+ business vocabulary items, {s['expression_count']} professional expressions
- Students produce their OWN sentences in every business scenario

## LANGUAGE LEVEL (CRITICAL)
{diff}
ALL content MUST match this level. This is BUSINESS English for the KSA workplace.

## Real Syllabus Data (use these — don't invent)

Sentences students will say in the workplace:
{sentences}

Business scenarios:
{themes}

Sample vocabulary: {vocab_sample}

Spiral layers (fixed): {", ".join(SPIRAL_NAMES)}

## Output this JSON (fill ALL values):

```json
{{
  "hero_line": "ONE bold career-aspirational one-liner. Max 12 words.",
  "spiral_scenario": "ONE real business scenario name from the syllabus above",
  "spiral_examples": [
    "Step 1 - simplest workplace phrase, 3-5 words",
    "Step 2 - add detail, 5-8 words",
    "Step 3 - formal/professional version, 6-10 words",
    "Step 4 - with adaptation, 6-12 words",
    "Step 5 - question form, 5-10 words",
    "Step 6 - full professional sentence, 8-18 words"
  ],
  "scenario_tags": [
    "Business scenario 1", "Business scenario 2", "Business scenario 3", "Business scenario 4", "Business scenario 5"
  ],
  "progress_text": "L{lv} of 15. Next: one-line career promise",
  "footer_cta": "Bold career CTA, 6-10 words",
  "footer_tagline": "Supporting career tagline, 5-10 words"
}}
```

RULES:
- hero_line: Career-aspirational. Professional. A workplace promise.
- spiral_examples: SAME business scenario across ALL 6 steps. Match {cefr_band} difficulty.
- scenario_tags: From syllabus. Use Saudi business context (KSU, STC, Aramco, Jarir, Vision 2030, etc.).
- progress_text: Career advancement promise for next level.
- footer: Professional, powerful, Saudi career focused.

Output JSON now:"""

async def call_api(s, cefr):
    sn = f"L{s['level_num']}"
    prompt = build_prompt(s, cefr)
    try:
        resp = await client.chat.completions.create(
            model="gemini-3.5-flash",
            messages=[
                {"role": "system", "content": "You are a business education copywriter. Output valid JSON only. No markdown fences. Start with { and end with }."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7, max_tokens=4096,
        )
        raw = resp.choices[0].message.content.strip()
        for pfx in ["```json", "```JSON", "```"]:
            if raw.startswith(pfx): raw = raw[len(pfx):]
        if raw.endswith("```"): raw = raw[:-3]
        data = json.loads(raw.strip())
        for f in ["hero_line","spiral_scenario","spiral_examples","scenario_tags","progress_text","footer_cta","footer_tagline"]:
            if f not in data: print(f"  [{sn}] MISSING:{f}"); return None
        assert len(data["spiral_examples"]) == 6
        print(f"  [{sn}] API OK")
        return {"sn": sn, "data": data, "stats": s, "cefr": cefr}
    except Exception as e:
        print(f"  [{sn}] API ERR: {str(e).encode('ascii', 'replace').decode()}")
        return None

HERO_SVG = """<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg" style="width:220px;height:200px;display:block">
<defs>
  <radialGradient id="bg" cx="58%" cy="42%">
    <stop offset="0%" stop-color="#1a4fc4" stop-opacity=".32"/>
    <stop offset="100%" stop-color="#040e2c" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect width="220" height="200" fill="url(#bg)"/>
<!-- desk -->
<rect x="20" y="150" width="180" height="9" rx="4.5" fill="#0d2060"/>
<rect x="20" y="150" width="180" height="2" rx="1" fill="#1e3a8a" opacity=".5"/>
<!-- laptop screen frame -->
<rect x="44" y="50" width="132" height="88" rx="7" fill="#071440" stroke="#1e3a8a" stroke-width="1.5"/>
<!-- screen glass -->
<rect x="49" y="55" width="122" height="76" rx="3" fill="#060e30"/>
<!-- left pane: teacher -->
<rect x="50" y="56" width="60" height="74" fill="#0c1e55"/>
<circle cx="80" cy="76" r="13" fill="#2563eb" opacity=".8"/>
<ellipse cx="80" cy="100" rx="19" ry="12" fill="#1d4ed8" opacity=".65"/>
<circle cx="53" cy="59" r="4" fill="#22c55e"/>
<!-- audio bars -->
<rect x="96" y="84" width="3" height="10" rx="1.5" fill="#60a5fa" opacity=".8"/>
<rect x="101" y="79" width="3" height="20" rx="1.5" fill="#60a5fa"/>
<rect x="106" y="87" width="3" height="8"  rx="1.5" fill="#60a5fa" opacity=".7"/>
<!-- right pane: student -->
<rect x="111" y="56" width="59" height="74" fill="#080e38"/>
<circle cx="140" cy="76" r="12" fill="#c47a3e" opacity=".9"/>
<ellipse cx="140" cy="99" rx="17" ry="11" fill="#1e3a6e" opacity=".85"/>
<rect x="137" y="85" width="6" height="13" rx="1.5" fill="#fff" opacity=".13"/>
<!-- call controls bar -->
<rect x="50" y="122" width="120" height="8" fill="#060e30"/>
<circle cx="100" cy="126" r="3.5" fill="#ef4444" opacity=".8"/>
<circle cx="110" cy="126" r="3.5" fill="#22c55e" opacity=".8"/>
<circle cx="120" cy="126" r="3.5" fill="#3b82f6" opacity=".8"/>
<!-- hinge -->
<rect x="40" y="136" width="140" height="5" rx="2.5" fill="#0a1e5c"/>
<!-- keyboard base -->
<rect x="34" y="140" width="152" height="11" rx="5" fill="#0d2468"/>
<rect x="50" y="143" width="90" height="2" rx="1" fill="#1a3a8a" opacity=".45"/>
<rect x="50" y="147" width="74" height="2" rx="1" fill="#1a3a8a" opacity=".35"/>
<!-- person -->
<ellipse cx="110" cy="172" rx="40" ry="18" fill="#1e3a6e"/>
<rect x="105" y="151" width="10" height="17" rx="2" fill="#fff" opacity=".1"/>
<rect x="104" y="139" width="12" height="16" rx="6" fill="#c47a3e"/>
<circle cx="110" cy="127" r="15" fill="#c47a3e"/>
<ellipse cx="110" cy="113" rx="15.5" ry="9" fill="#1a1a1a" opacity=".82"/>
<path d="M95,123 Q110,111 125,123" stroke="#1a1a1a" stroke-width="5" fill="none" stroke-linecap="round" opacity=".8"/>
<ellipse cx="95" cy="127" rx="3" ry="4.5" fill="#b87040" opacity=".75"/>
<ellipse cx="125" cy="127" rx="3" ry="4.5" fill="#b87040" opacity=".75"/>
<!-- speech bubble -->
<rect x="128" y="14" width="86" height="42" rx="9" fill="#ffed6e"/>
<polygon points="141,56 151,56 146,65" fill="#ffed6e"/>
<text x="136" y="31" font-family="'Segoe UI',system-ui,sans-serif" font-size="9" font-weight="700" fill="#1a1a2e">Good morning,</text>
<text x="136" y="45" font-family="'Segoe UI',system-ui,sans-serif" font-size="9" font-weight="600" fill="#2d3748">I'm ready to speak.</text>
<!-- sparkles -->
<circle cx="28" cy="36" r="2.5" fill="#ffed6e" opacity=".45"/>
<circle cx="15" cy="62" r="1.5" fill="#60a5fa" opacity=".35"/>
<circle cx="208" cy="158" r="2" fill="#ffed6e" opacity=".3"/>
</svg>"""


def fill_template(sn, data, s, cefr_band):
    with open(os.path.join(WORK_DIR, "be_poster_template.html"), "r", encoding="utf-8") as f:
        html = f.read()

    lv = s["level_num"]

    # Condensed 3-phase spiral
    phases_html = ""
    for pi, (phase_name, bg, txt) in enumerate(SPIRAL_PHASES):
        s1, s2 = SPIRAL_NAMES[pi * 2], SPIRAL_NAMES[pi * 2 + 1]
        ex = data["spiral_examples"][pi * 2]
        phases_html += (
            f'<div class="phase-pill" style="background:{bg}">'
            f'<div class="name" style="color:{txt}">{phase_name}</div>'
            f'<div class="steps"><span>{s1}</span> · <span>{s2}</span></div>'
            f'<div class="ex">"{ex}"</div>'
            f'</div>'
        )
        if pi < 2:
            phases_html += '<div class="phase-arrow">→</div>'

    tags_html = "".join(f'<span class="tag">{t}</span>' for t in data["scenario_tags"])
    dots_html = "".join(f'<div class="dot{"" if i > lv else " on"}"></div>' for i in range(1, 16))

    pg = BE_PAIN_POINTS[lv]

    html = html.replace("{{COURSE_NAME}}", COURSE_NAME)
    html = html.replace("{{LEVEL}}", sn)
    html = html.replace("{{CEFR}}", cefr_band)
    html = html.replace("{{HERO_LINE}}", data["hero_line"])
    html = html.replace("{{HERO_SUB}}", BE_HERO_SUB[lv])
    html = html.replace("{{HERO_SVG}}", HERO_SVG)
    html = html.replace("{{PAIN_Q}}", pg["question"])
    html = html.replace("{{PAIN_CTA}}", pg["cta"])
    html = html.replace("{{SCENARIO_COUNT}}", str(s["unit_count"]))
    html = html.replace("{{EXAMPLE_SCENARIO}}", data["spiral_scenario"])
    html = html.replace("{{SPIRAL_PHASES_HTML}}", phases_html)
    html = html.replace("{{SCENARIO_TAGS}}", tags_html)
    html = html.replace("{{PROGRESS_DOTS}}", dots_html)
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

async def main():
    print("Extracting BE stats...")
    stats = extract_be_stats()
    cefr = GE_CEFR
    items = [(sn, stats[sn], cefr[stats[sn]["level_num"]]) for sn in sorted(stats.keys(), key=lambda x: int(x[1:]))]
    for sn, s, c in items:
        print(f"  {sn}: {s['lesson_count']}L, {s['total_vocab_count']}w+, {s['expression_count']}e")

    print(f"\n=== Phase 1: {len(items)} API calls in parallel ===")
    results = await asyncio.gather(*[call_api(s, c) for _, s, c in items])
    results = [r for r in results if r is not None]
    print(f"  {len(results)}/{len(items)} API calls succeeded")

    print(f"\n=== Phase 2: Fill templates ===")
    html_files = []
    for r in results:
        sn, data, s, (cefr_band, _, _) = r["sn"], r["data"], r["stats"], r["cefr"]
        html = fill_template(sn, data, s, cefr_band)
        hf = os.path.join(OUT_DIR, f"BE_{sn}_poster.html")
        with open(hf, "w", encoding="utf-8") as f: f.write(html)
        html_files.append((sn, hf))
        print(f"  [{sn}] HTML saved")

    print(f"\n=== Phase 3: {len(html_files)} PNG renders in parallel ===")
    def render_one(sn, hf):
        pf = os.path.join(OUT_DIR, f"BE_{sn}_poster.png")
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
