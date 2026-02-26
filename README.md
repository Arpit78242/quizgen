# QuizGen — AI-Powered Quiz Generation Platform

FastAPI + PostgreSQL + HuggingFace backend for generating MCQ quizzes from PDFs, DOCX, images, or any topic.

---

## Tech Stack
- **Backend**: FastAPI
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Frontend**: Jinja2 HTML + Vanilla CSS/JS
- **AI**: HuggingFace Inference API via `huggingface-hub`
- **File Extraction**: LangChain (PDF, DOCX, Image/OCR)

---

## Project Structure
```
quizgen/
├── main.py                  # App entrypoint
├── core/
│   ├── config.py            # Settings (env vars)
│   ├── security.py          # JWT + bcrypt
│   └── dependencies.py      # FastAPI deps (get_db, get_current_user)
├── db/
│   ├── base.py              # SQLAlchemy engine + session
│   └── schema.sql           # Raw SQL schema (optional reference)
├── models/                  # SQLAlchemy ORM models
├── schemas/                 # Pydantic schemas
├── routers/                 # FastAPI route handlers
├── services/                # Business logic
├── templates/               # Jinja2 HTML
└── static/                  # CSS + JS
```

---

## Setup

### 1. Clone and install dependencies
```bash
cd quizgen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your values:
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Random string for JWT signing (min 32 chars) |
| `HF_API_TOKEN` | Your HuggingFace API token |
| `HF_MODEL_ID` | HuggingFace model ID (default: Qwen/Qwen2.5-72B-Instruct) |

### 3. Create the database
```bash
# In PostgreSQL:
createdb quizgen

# Tables are auto-created on first run via SQLAlchemy
# Or run manually:
psql quizgen < db/schema.sql
```

### 4. Run the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000

---

## Features
- **Auth**: Register/login with JWT stored in httpOnly cookies
- **Sources**: Upload PDF, DOCX, images (OCR via pytesseract) or enter any topic
- **Quiz Generation**: AI generates 1–10 MCQ questions with 4 options each
- **Timer**: User sets their own time limit; countdown auto-submits when expired
- **Results**: Scores, percentages, per-question review with correct/wrong highlighting
- **History**: Full paginated history of all past quiz attempts

---

## HuggingFace Model Note
The default model is `Qwen/Qwen2.5-72B-Instruct`. You can change this in `.env`.
Make sure your HuggingFace token has Inference API access enabled.

For OCR (image extraction), install Tesseract:
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Windows: download installer from https://github.com/UB-Mannheim/tesseract/wiki
```
