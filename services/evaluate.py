import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
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


