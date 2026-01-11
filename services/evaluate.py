import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """
You are a senior ICMAI-certified examiner.

STRICT RULES:
- Award marks ONLY for content explicitly written.
- Do NOT assume intent or missing steps.
- Do NOT reward length or generic knowledge.
- Partial marks only if concept/step is partially correct.
- Incorrect concepts get zero marks.
- No negative marking.
- Follow marking scheme strictly.
- Be conservative.
- Respond in STRICT JSON only.
"""


def safe_json_loads(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("LLM returned empty response")

    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if not match:
        raise ValueError(f"No JSON found in LLM output:\n{text}")

    return json.loads(match.group(1))


def generate_ca_icmai_evaluation_prompt(question: str, answer: str) -> str:
    """
    Generates a Groq prompt to evaluate CA answers
    strictly as per ICMAI / ICAI evaluation guidelines.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
You are a senior ICMAI-certified examiner evaluating a Chartered Accountancy answer.

Evaluate the student's answer STRICTLY based on ICMAI/ICAI examination standards.

### ICMAI Evaluation Guidelines
- Focus on **conceptual correctness**
- Credit **relevant points even if language is imperfect**
- Do NOT assume missing facts
- Step-wise and point-wise answers score higher
- Give partial marks where applicable
- Penalize irrelevance and incorrect concepts
- Professional presentation matters (clarity, structure)

### Question
{question}

### Student Answer
{answer}

### Evaluation Criteria
Assess the answer on:
1. Conceptual Accuracy
2. Coverage of Key Points
3. Logical Structure & Presentation
4. Relevance to the Question
5. Professional Language (not grammar perfection)

### Output Format (STRICT JSON ONLY)
{{
  "total_marks": 10,
  "marks_awarded": "<number between 0 and 10>",
  "verdict": "<Excellent | Good | Average | Poor | Incorrect>",
  "conceptual_accuracy": "<brief evaluation>",
  "key_points_covered": "<list or short description>",
  "missing_or_incorrect_points": "<what is missing or wrong>",
  "presentation_feedback": "<structure, clarity, step-wise comments>",
  "examiner_remarks": "<ICMAI-style concise remark>"
}}
"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # Validate and parse JSON
    try:
        parsed = json.loads(content)

        return {
            "total_marks": parsed.get("total_marks", 10),
            "marks_awarded": parsed.get("marks_awarded", 0),
            "verdict": parsed.get("verdict", ""),
            "conceptual_accuracy": parsed.get("conceptual_accuracy", ""),
            "key_points_covered": parsed.get("key_points_covered", ""),
            "missing_or_incorrect_points": parsed.get("missing_or_incorrect_points", ""),
            "presentation_feedback": parsed.get("presentation_feedback", ""),
            "examiner_remarks": parsed.get("examiner_remarks", "")
        }

    except json.JSONDecodeError:
        # Hard fallback — prevents pipeline crash
        return {
            "total_marks": 10,
            "marks_awarded": 0,
            "verdict": "",
            "conceptual_accuracy": "",
            "key_points_covered": "",
            "missing_or_incorrect_points": "",
            "presentation_feedback": "",
            "examiner_remarks": ""
        }


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def decompose_answer(question: str, answer: str) -> dict:
    """ Stage 1 — Answer Decomposition
    Decomposes a student's answer into discrete examinable points."""

    prompt = f"""
You are performing ONLY answer decomposition.

Task:
Break the student's answer into discrete examinable points or steps.

Rules:
- Do NOT evaluate correctness.
- Do NOT award marks.
- Do NOT infer missing intent.
- Capture points exactly as written.

Question:
{question}

Student Answer:
{answer}

Output Format (STRICT JSON):
{{
  "identified_points": [
    {{
      "point_text": "",
      "type": "definition | explanation | step | calculation | conclusion",
      "is_stepwise": true
    }}
  ],
  "irrelevant_or_wrong_points": []
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)


def map_to_marking_scheme(extracted_points: dict, marking_scheme) -> dict:
    prompt = f"""
You are an ICMAI examiner performing ONLY marking-scheme mapping.

TASK:
For each student point, determine:
1. Whether it matches a marking-scheme point.
2. If it does NOT match, which scheme point it is closest to (if any).

STRICT RULES:
- Do NOT award marks.
- Do NOT infer intent.
- Match ONLY what is explicitly written.
- If the point is irrelevant, use closest_point_code = null.
- If nothing matches, set point_code = "no_match".
- Return STRICT JSON only.
- No explanations.

MARKING SCHEME (AUTHORITATIVE):
{json.dumps([p.dict() for p in marking_scheme.scheme], indent=2)}

STUDENT EXTRACTED POINTS:
{json.dumps(extracted_points["identified_points"], indent=2)}

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "mapping": [
    {{
      "student_point": "",
      "point_code": "",
      "closest_point_code": null,
      "match_type": "exact | partial | no_match"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return safe_json_loads(response.choices[0].message.content)


def calculate_marks(mapping_result: dict, marking_scheme) -> dict:
    scheme_map = {
        p.point_code: p.max_marks
        for p in marking_scheme.scheme
    }

    awarded = 0
    breakdown = []
    seen_points = set()

    # 1️⃣ Process matched student points
    for item in mapping_result["mapping"]:
        point_code = item["point_code"]
        match_type = item["match_type"]

        if point_code in seen_points:
            continue
        seen_points.add(point_code)

        max_marks = scheme_map.get(point_code, 0)

        if match_type == "exact":
            marks = max_marks
        elif match_type == "partial":
            marks = max_marks * 0.5
        else:
            marks = 0

        awarded += marks

        breakdown.append({
            "scheme_point": point_code,
            "student_point": item["student_point"],
            "marks_awarded": marks,
            "max_marks": max_marks,
            "status": "attempted" if marks > 0 else "attempted_but_not_awarded"
        })

    # 2️⃣ Add UNATTEMPTED scheme points
    for scheme_point, max_marks in scheme_map.items():
        if scheme_point not in seen_points:
            breakdown.append({
                "scheme_point": scheme_point,
                "student_point": None,
                "marks_awarded": 0,
                "max_marks": max_marks,
                "status": "not_attempted"
            })

    awarded = min(awarded, marking_scheme.total_marks)

    return {
        "total_marks": marking_scheme.total_marks,
        "marks_awarded": round(awarded, 2),
        "breakdown": breakdown
    }


def derive_verdict(marks: float, total: float) -> str:
    """ Derive verdict based on marks ratio """

    ratio = marks / total
    if ratio >= 0.8:
        return "Excellent"
    elif ratio >= 0.6:
        return "Good"
    elif ratio >= 0.4:
        return "Average"
    elif ratio >= 0.2:
        return "Poor"
    return "Incorrect"


def generate_examiner_feedback(
        question: str,
        score_summary: dict,
        breakdown: list
) -> dict:
    """ Stage 4 — Examiner Feedback Generation """

    prompt = f"""
Prepare an ICMAI-style examiner evaluation summary.

Question:
{question}

Marks Awarded:
{score_summary["marks_awarded"]} / {score_summary["total_marks"]}

Breakdown:
{json.dumps(breakdown, indent=2)}

Output Format (STRICT JSON):
{{
  "conceptual_accuracy": "",
  "key_points_covered": "",
  "missing_or_incorrect_points": "",
  "presentation_feedback": "",
  "examiner_remarks": ""
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return safe_json_loads(response.choices[0].message.content)


def evaluate_ca_answer_experimental(
        question: str,
        answer: str,
        marking_scheme
) -> dict:
    """ Full Evaluation Pipeline for CA Answers """

    extracted = decompose_answer(question, answer)

    mapped = map_to_marking_scheme(extracted, marking_scheme)

    scoring = calculate_marks(mapped, marking_scheme)

    feedback = generate_examiner_feedback(
        question,
        scoring,
        scoring["breakdown"]
    )

    verdict = derive_verdict(
        scoring["marks_awarded"],
        scoring["total_marks"]
    )

    return {
        "total_marks": scoring["total_marks"],
        "marks_awarded": scoring["marks_awarded"],
        "verdict": verdict,
        **feedback,
        "marking_breakdown": scoring["breakdown"]
    }


def generate_icmai_marking_scheme(question: str, total_marks: int):
    prompt = f"""
You are a senior ICMAI-certified examiner preparing an OFFICIAL marking scheme
for a Chartered Accountancy (CA) descriptive examination question.

Your task is to generate an ICMAI-SAFE marking scheme.

STRICT ICMAI RULES (VERY IMPORTANT):
- Assume students may write answers in imperfect language.
- Do NOT include points that are OPTIONAL, ADVANCED, or BEYOND the question.
- Do NOT include comparison unless explicitly asked.
- Do NOT include numerical formulas unless they are CORE to the concept.
- Prefer high-level examinable ideas used in official ICMAI/ICAI solutions.
- Each point must be:
  - Conceptually essential
  - Independently assessable
  - Commonly rewarded in ICMAI exams
- Avoid over-fragmentation (too many small points).
- Allow partial understanding to earn marks.
- Ensure no point unfairly causes zero scoring.

MARK DISTRIBUTION RULES:
- Total marks = {total_marks}
- Use 4–6 examiner points ONLY (recommended for 8–10 mark questions)
- Each point should carry 1–3 marks
- Sum of all max_marks MUST equal {total_marks}

POINT CODING RULES:
- Use short, examiner-style codes (e.g., MC_DEF, MC_VAR, MC_FIXED)
- Codes must reflect the CONCEPT, not numbering

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "total_marks": {total_marks},
  "scheme": [
    {{
      "point_code": "CODE",
      "description": "What the examiner explicitly looks for",
      "max_marks": integer
    }}
  ]
}}

QUESTION (AUTHORITATIVE):
{question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return safe_json_loads(response.choices[0].message.content)
