"""Extract BE stats per level from BE Levels sheet."""
import re, json, openpyxl

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

wb = openpyxl.load_workbook("KSA BE 20260324.xlsx", data_only=True)
ws = wb["BE Levels"]

phases = {}
current = None
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
    r0 = str(row[0]).strip() if row[0] else ""
    if r0.startswith("Phase"):
        current = r0
        phases[current] = {"units": [], "all_vocab": set(), "all_sentences": [], "themes": []}
    elif current and r0.isdigit() and 1 <= int(r0) <= 8:
        theme = str(row[1])[:150] if len(row) > 1 and row[1] else ""
        vocab_raw = str(row[3]) if len(row) > 3 and row[3] else ""
        sent_raw = str(row[4]) if len(row) > 4 and row[4] else ""

        for v in re.split(r'[,.\-]', vocab_raw):
            v = v.strip().lower()
            if v and len(v) > 1 and v not in STOPWORDS:
                phases[current]["all_vocab"].add(v)

        for line in sent_raw.split("\n"):
            s = re.sub(r'^[\-\s]+', '', line).strip().strip('"')
            if s and len(s) > 8:
                phases[current]["all_sentences"].append(s[:150])

        phases[current]["themes"].append(theme)
        phases[current]["units"].append({"theme": theme})

wb.close()

result = {}
def phase_num(pn):
    return int(re.match(r'Phase (\d+)', pn).group(1))

for i, pn in enumerate(sorted(phases.keys(), key=phase_num), 1):
    p = phases[pn]
    unique_s = list(dict.fromkeys(p["all_sentences"]))
    result[f"L{i}"] = {
        "vocab": len(p["all_vocab"]),
        "expressions": len(unique_s),
        "units": len(p["units"]),
        "themes": p["themes"][:5],
        "sample_sentences": unique_s[:4],
        "sample_vocab": sorted(p["all_vocab"])[:15],
    }

with open("output/_be_stats.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

for sn in sorted(result.keys(), key=lambda x: int(x[1:])):
    r = result[sn]
    print(f"{sn}: {r['units']}u, {r['vocab']}w, {r['expressions']}e")
    print(f"  Themes: {r['themes'][:3]}")
    print(f"  S: {r['sample_sentences'][:2]}")
