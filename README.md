# EvalCA Backend 🚀  
**AI-Powered Descriptive Answer Evaluation Platform**

EvalCA is a FastAPI-based backend system designed to evaluate Chartered Accountancy (CA) descriptive answers using OCR and LLM-based reasoning.  
It combines PaddleOCR for document text extraction, Groq LLM (GPT-OSS model) for intelligent evaluation, and a Supabase/PostgreSQL-backed database.

---

## ✨ Key Features

- JWT-based Authentication & Role-Based Authorization  
- OCR-powered question & answer extraction using PaddleOCR  
- LLM-driven evaluation via Groq (GPT-OSS)  
- Configurable validation limits (files, word counts)  
- Role-based access control (Student / Teacher / Admin)  
- PostgreSQL database (Supabase compatible)  
- Clean FastAPI architecture

---

## 🛠 Tech Stack

- **Backend:** FastAPI  
- **OCR:** PaddleOCR  
- **LLM:** Groq (GPT-OSS)  
- **Database:** PostgreSQL (Supabase)  
- **ORM:** SQLAlchemy  
- **Auth:** JWT  
- **Language:** Python 3.10+

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
DISABLE_MODEL_SOURCE_CHECK=
GROQ_API_KEY=

FRONTEND_BASE_API=

MAXIMUM_QUESTION_FILES=
MAXIMUM_ANSWER_FILES=

MAX_TOTAL_WORDS=
MAX_QUESTION_WORDS=
MAX_ANSWER_WORDS=

USER=
PASSWORD=
HOST=
PORT=
DBNAME=

SECRET_KEY=
```

---

## 📦 Installation

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Server

Use FastAPI CLI:

```bash
fastapi dev main.py
```

API:
```
http://127.0.0.1:8000
```

Docs:
```
http://127.0.0.1:8000/docs
```

---

## 🧠 Evaluation Flow

1. Upload question & answer  
2. OCR extracts text  
3. Validation checks  
4. Groq LLM evaluates answer  
5. Score & feedback returned  

---

## 📄 License

MIT License
