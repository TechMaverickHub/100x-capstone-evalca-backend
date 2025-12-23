import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def detect_question_answer(text: str):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
You are an information extraction assistant.

Your task is to read the input text and:

- Extract the exact text span that represents the question
- Extract the exact text span that represents the answer

Rules (VERY IMPORTANT):
- Do NOT rewrite, rephrase, summarize, or infer
- Return text exactly as it appears in the input
- Only extract contiguous text spans
- If multiple questions or answers exist, extract the primary one
- If a part is missing, return an empty string ""

Output Format (JSON only):
{{
  "question": "",
  "answer": ""
}}

### Examples

Input:
What is Python?
Python is a high-level programming language.

Output:
{{
  "question": "What is Python?",
  "answer": "Python is a high-level programming language."
}}

---

Input:
Can you explain REST APIs?
REST APIs allow systems to communicate over HTTP using standard methods.

Output:
{{
  "question": "Can you explain REST APIs?",
  "answer": "REST APIs allow systems to communicate over HTTP using standard methods."
}}

---

Input:
This document explains neural networks and their applications.

Output:
{{
  "question": "",
  "answer": ""
}}

---

### Input Text
{text}
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
            "question": parsed.get("question", ""),
            "answer": parsed.get("answer", "")
        }
    except json.JSONDecodeError:
        # Hard fallback to safe empty output
        return {
            "question": "",
            "answer": ""
        }
