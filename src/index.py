#!/usr/bin/env python3
"""
thumbnail-analyzer — YouTube thumbnail image → CTR score, design analysis,
contrast check, text readability, emotion analysis, improvement suggestions,
A/B test recommendations
"""
import anthropic, base64, json, re, sys
from pathlib import Path

SYSTEM = """You are a YouTube growth strategist and visual design expert who has analyzed
millions of thumbnails and understands exactly what drives click-through rates.

Analyze this thumbnail with brutal honesty. CTR is everything.

Return ONLY valid JSON — no markdown, no explanation.

{
  "ctr_score": number_0_to_100,
  "ctr_grade": "A|B|C|D|F",
  "verdict": "one sentence honest assessment",
  "visual_analysis": {
    "dominant_colors": ["list of hex codes or color names"],
    "color_contrast": "excellent|good|poor|very_poor",
    "brightness": "bright|normal|dark",
    "background_complexity": "clean|moderate|busy|cluttered",
    "has_face": true_or_false,
    "face_emotion": "excited|shocked|curious|serious|happy|angry|fear|null",
    "face_size": "large|medium|small|null",
    "eye_contact": true_or_false,
    "has_text": true_or_false,
    "text_word_count": number,
    "text_readability": "excellent|good|poor|unreadable|null",
    "text_size": "large|medium|small|null",
    "text_color_contrast": "high|medium|low|null",
    "main_subject_clarity": "very_clear|clear|unclear|chaotic"
  },
  "psychological_triggers": {
    "curiosity_gap": true_or_false,
    "social_proof": true_or_false,
    "urgency": true_or_false,
    "fear_of_missing_out": true_or_false,
    "aspirational": true_or_false,
    "controversy": true_or_false,
    "humor": true_or_false,
    "before_after": true_or_false
  },
  "what_works": ["specific things that are effective"],
  "what_doesnt_work": ["specific weaknesses — be direct"],
  "improvements": [
    {
      "priority": "critical|high|medium|low",
      "change": "specific actionable change",
      "expected_ctr_lift": "low|medium|high|very_high",
      "why": "psychological reason this works"
    }
  ],
  "text_copy_feedback": {
    "current_text": "extracted text or null",
    "issues": ["list of issues with current text"],
    "suggested_text": ["2-3 alternative text overlays that would perform better"]
  },
  "ab_test_suggestions": [
    {
      "test_hypothesis": "what you're testing",
      "variant_a": "current or description",
      "variant_b": "proposed change",
      "expected_winner": "A|B|unclear"
    }
  ],
  "benchmark_comparison": {
    "performs_like": "top_10pct|top_25pct|average|below_average|bottom_25pct",
    "similar_high_performing_pattern": "description of what high-performing thumbnails in this niche look like"
  },
  "mobile_optimization": {
    "readable_on_mobile": true_or_false,
    "issues": ["list of mobile-specific issues"]
  },
  "niche_fit": "well_suited|neutral|poor_fit for typical video thumbnails"
}"""

def analyze(image_source: str) -> dict:
    client = anthropic.Anthropic()
    path = Path(image_source)

    if path.exists():
        suffix = path.suffix.lower()
        mt = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
              ".webp":"image/webp",".gif":"image/gif"}.get(suffix,"image/jpeg")
        data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        content = [
            {"type":"image","source":{"type":"base64","media_type":mt,"data":data}},
            {"type":"text","text":"Analyze this YouTube thumbnail for CTR optimization."}
        ]
    elif image_source.startswith("http"):
        content = [
            {"type":"image","source":{"type":"url","url":image_source}},
            {"type":"text","text":"Analyze this YouTube thumbnail for CTR optimization."}
        ]
    else:
        raise ValueError("Provide an image file path or URL")

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=2000, system=SYSTEM,
        messages=[{"role":"user","content":content}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

GRADE_C = {"A":"\033[92m","B":"\033[92m","C":"\033[93m","D":"\033[91m","F":"\033[91m"}
R = "\033[0m"
PRI_ICON = {"critical":"🚨","high":"🔴","medium":"🟡","low":"🔵"}
LIFT_ICON = {"very_high":"🚀","high":"📈","medium":"📊","low":"➡"}

def print_report(r: dict):
    vis = r.get("visual_analysis",{})
    psych = r.get("psychological_triggers",{})
    grade = r.get("ctr_grade","?")
    score = r.get("ctr_score",0)
    bench = r.get("benchmark_comparison",{})

    print(f"\n{'═'*60}")
    print(f"  THUMBNAIL ANALYZER")
    print(f"  CTR Score: {GRADE_C.get(grade,'')}{grade}{R} ({score}/100)")
    print(f"  {r.get('verdict','')}")
    print(f"{'═'*60}")

    print(f"\n  VISUAL PROFILE")
    score_bar = "█"*(score//10) + "░"*(10-score//10)
    print(f"  [{score_bar}] {score}/100 | {bench.get('performs_like','?').replace('_',' ')}")
    print(f"\n  Face: {'✅ ' + vis.get('face_emotion','?') if vis.get('has_face') else '❌ No face'}")
    print(f"  Eye contact: {'✅' if vis.get('eye_contact') else '❌'}")
    print(f"  Text: {vis.get('text_word_count',0)} words | Readability: {vis.get('text_readability','?')}")
    print(f"  Contrast: {vis.get('color_contrast','?')} | Background: {vis.get('background_complexity','?')}")
    print(f"  Main subject: {vis.get('main_subject_clarity','?')}")

    active_triggers = [k.replace('_',' ') for k,v in psych.items() if v]
    if active_triggers: print(f"\n  Triggers: {', '.join(active_triggers)}")

    works = r.get("what_works",[])
    if works:
        print(f"\n  WHAT'S WORKING")
        for w in works: print(f"  ✅ {w}")

    problems = r.get("what_doesnt_work",[])
    if problems:
        print(f"\n  WHAT'S NOT WORKING")
        for prob in problems: print(f"  ❌ {prob}")

    improvements = r.get("improvements",[])
    if improvements:
        sorted_imp = sorted(improvements, key=lambda x: ["critical","high","medium","low"].index(x.get("priority","low")))
        print(f"\n  IMPROVEMENTS (ranked by impact)")
        for imp in sorted_imp:
            lift = LIFT_ICON.get(imp.get("expected_ctr_lift","low"),"")
            print(f"\n  {PRI_ICON.get(imp.get('priority','low'),'')} {lift} {imp.get('change','')}")
            print(f"     Why: {imp.get('why','')}")

    text_fb = r.get("text_copy_feedback",{})
    suggested = text_fb.get("suggested_text",[])
    if suggested:
        print(f"\n  BETTER TEXT OVERLAYS")
        for t in suggested: print(f"  • \"{t}\"")

    ab = r.get("ab_test_suggestions",[])
    if ab:
        print(f"\n  A/B TESTS TO RUN")
        for test in ab[:2]:
            print(f"  Test: {test.get('test_hypothesis','')}")
            print(f"  A: {test.get('variant_a','')} vs B: {test.get('variant_b','')}")
            print(f"  Predicted winner: {test.get('expected_winner','?')}")

    mobile = r.get("mobile_optimization",{})
    if not mobile.get("readable_on_mobile"):
        print(f"\n  ⚠ MOBILE ISSUES")
        for iss in mobile.get("issues",[]): print(f"  ! {iss}")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Analyze YouTube thumbnail for CTR optimization")
    p.add_argument("image", help="Image file path or URL")
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    r = analyze(a.image)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
