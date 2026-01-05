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



def map_to_marking_scheme(extracted_points: dict, marking_scheme: dict) -> dict:
    prompt = f"""
You are an ICMAI examiner performing ONLY scheme mapping.

TASK:
For each student point, identify whether it matches a marking-scheme point.

RULES (VERY IMPORTANT):
- Match ONLY what is explicitly written.
- Do NOT infer intent.
- Do NOT award marks.
- Do NOT invent scheme points.
- If nothing matches, return "no_match".
- Return STRICT JSON ONLY.
- Do NOT include explanations.

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
    """
    Stage 3 — Deterministic marks calculation
    """

    scheme_map = {
        p.point_code: p.max_marks
        for p in marking_scheme.scheme
    }

    awarded = 0
    breakdown = []
    seen_points = set()

    for item in mapping_result["mapping"]:
        point_code = item["point_code"]
        match_type = item["match_type"]

        # prevent double counting
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
            "student_point": item["student_point"],
            "scheme_point": point_code,
            "marks_awarded": marks,
            "max_marks": max_marks
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

    print("Before prompt")
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

    print("after prompt")

    print(prompt)

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

    print("decomposing answer")
    extracted = decompose_answer(question, answer)

    print("text extracted")
    mapped = map_to_marking_scheme(extracted, marking_scheme)

    print("mapping done")
    scoring = calculate_marks(mapped, marking_scheme)

    print("marks calculated")
    feedback = generate_examiner_feedback(
        question,
        scoring,
        scoring["breakdown"]
    )

    print("feedback generated")

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
