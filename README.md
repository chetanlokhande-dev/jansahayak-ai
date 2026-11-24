# JanSahayak AI

**Government Information. Simplified for Everyone.**

An AI-powered web app that explains Indian government schemes, official notices and basic legal rights in simple language, in **English, Hindi and Marathi**, with official source links.

> **Independent helper. Not an official government website and not legal advice.**
> The scheme and rights data shipped in this repo is **SAMPLE data for development and testing**. Replace it with data from verified official sources before any real deployment (see [Replacing the sample data](#replacing-the-sample-data)).

## Features

| Area | What it does |
|---|---|
| AI Assistant | Chat with follow-up questions. Answers are grounded in retrieved sources and split into **verified / inferred / unavailable**. |
| Document Explainer | Upload PDF, DOCX, TXT or an image (OCR). Get a simple summary, key points, required documents, dates and amounts, next steps and what is unclear. Then ask questions about it. |
| Scheme Finder | Browse and search schemes with benefits, eligibility, documents, how to apply and the official link. |
| Eligibility Checker | Step-by-step questions evaluated by a **rule engine** (not the LLM). Every criterion shows met / not met / unknown. It never says "approved". |
| Rights Explorer | Plain-language summaries of basic rights (RTI, free legal aid, arrest, education, consumer, police complaint). |
| Voice | Speech-to-text input (Web Speech API) and read-aloud (Speech Synthesis). Needs a browser with speech support (Chrome / Edge). |
| History | Past chats and documents for this browser, with delete. |

**Works without a Gemini key.** With no key the backend runs in *offline mode*: answers come straight from the built-in knowledge base (English only) and documents get a basic extraction. Add a key to get conversational answers, translation and simplified document explanations.

## Project layout

```
jansahayak-ai/
├── backend/                 FastAPI app
│   ├── app/
│   │   ├── main.py          API routes, validation, rate limiting
│   │   ├── config.py        Settings from environment variables
│   │   ├── schemas.py       Request models
│   │   ├── data/            schemes.json, rights.json, sample_documents/   (ALL SAMPLE DATA)
│   │   └── services/
│   │       ├── documents.py     PDF / DOCX / TXT / image parsing + OCR (in memory only)
│   │       ├── retrieval.py     BM25 retrieval (RAG) over the knowledge base and uploaded docs
│   │       ├── eligibility.py   Structured rule engine
│   │       ├── gemini.py        Gemini REST client (key stays on the server)
│   │       ├── assistant.py     Prompting, grounding, offline fallback
│   │       └── store.py         SQLite history (per anonymous browser id)
│   ├── tests/               pytest suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/                React + Tailwind (Vite)
    └── src/ pages/ components/ lib/ context/
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- **Tesseract OCR** (for image/scanned-document text), plus Hindi and Marathi language packs:
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu/Debian: `sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar`
  - Windows: install from the [UW Mannheim builds](https://github.com/UB-Mannheim/tesseract/wiki), select Hindi and Marathi data, and add it to `PATH`.
- A Gemini API key (optional but recommended): <https://aistudio.google.com/apikey>

## Run locally

### ⚡ Quick Start (Single Command / One-Click)

The frontend is built and served directly by the FastAPI backend on a single port (`8000`). You **do not** need multiple terminals or separate servers to run this prototype!

#### Option A: Windows Double-Click
Double-click `run.bat` (or `start.bat`) in the root directory. It automatically starts the server and opens `http://localhost:8000` in your browser.

#### Option B: Terminal (Single Command)
From the project root:
```powershell
.\run.ps1
```
Or directly with Python:
```powershell
.\backend\.venv\Scripts\activate
uvicorn app.main:app --app-dir backend --port 8000
```
Then visit **http://localhost:8000** in your browser!

---

### 🛠️ Developer Mode (Separate Hot-Reloading Servers)

If you are developing new frontend UI components and want live hot-reloading:

1. **Backend**:
```bash
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

2. **Frontend**:
```bash
cd frontend
npm run dev
```
Visit http://localhost:5173 (Vite proxies all `/api` requests to backend at port 8000).

### 3. Tests

```bash
cd backend
pytest -q
```

`tests/test_api.py` is an end-to-end test of every route (chat, history, upload, eligibility, validation). It runs once FastAPI and httpx are installed.

## Manual test checklist

1. **Language**: switch English / हिन्दी / मराठी. Menus, buttons and the eligibility questions change language.
2. **Chat**: ask "What help is there for farmers?". Expect PM-KISAN, an official link and a sample-data tag. Ask a follow-up in the same chat.
3. **No-guess behaviour**: ask something unrelated ("best pizza topping"). Expect "I will not guess" and the official portals.
4. **Document**: go to *Documents*, click a sample, or upload your own PDF/DOCX/TXT/image. Check dates and amounts, then press *Ask questions about this document* and ask "What is the penalty?".
5. **Eligibility**: answer the questions, using *Not sure* for some. Those schemes should say *Need more details*, never *May qualify*.
6. **Voice**: press the mic on the Assistant, speak, then press *Listen* on an answer.
7. **History**: reopen a chat and delete it.
8. **Mobile**: open browser dev tools at ~375px wide. Nothing should scroll sideways.

## API summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health`, `/api/meta` | Status, languages, AI mode, official portals |
| GET | `/api/schemes`, `/api/schemes/{id}` | Scheme finder (`?q=`, `?category=`) |
| GET | `/api/rights`, `/api/rights/{id}` | Rights explorer |
| POST | `/api/chat` | Grounded chat `{message, language, conversation_id?, document_id?}` |
| POST | `/api/documents` | Upload (multipart `file`, `language`) and explain |
| GET/POST | `/api/sample-documents[/{name}]` | Fictional test documents |
| GET | `/api/eligibility/fields?lang=` | Question definitions |
| POST | `/api/eligibility/check` | Rule-based eligibility `{profile, language}` |
| POST | `/api/translate` | Translate text (needs Gemini) |
| GET/DELETE | `/api/history…`, `/api/documents/{id}` | History management |

Calls other than public data need an `X-Client-Id` header (the frontend creates a random id per browser and keeps it in `localStorage`).

## Security and privacy notes

- The Gemini key is read from the backend environment only; nothing secret is in the frontend bundle.
- Uploads are validated by extension **and** file content, capped by `MAX_UPLOAD_MB`, and processed **in memory** (no temp files are written). Extracted text is stored in SQLite only so you can ask follow-up questions, and can be deleted from History.
- History is scoped by an anonymous browser id. This is **not authentication**: anyone who obtains that id could read that history. Add real login before storing anything sensitive.
- Per-browser rate limiting is in-memory (single process). Use a shared store such as Redis if you run several workers.
- Model output is rendered as React text, never as raw HTML.

## Replacing the sample data

`backend/app/data/schemes.json` and `rights.json` are small, simplified, hand-written summaries to make the app runnable. They have **not** been verified against current official sources and will go out of date (amounts, rules and deadlines change). Before real use:

1. Ingest scheme and law text from the official sources (myScheme, India.gov.in, Legislative Department, PIB, NALSA), keeping each record's official URL and a "last verified" date.
2. Keep the same JSON shape, or adapt `knowledge.py` / `retrieval.py`. Structured `criteria` / `exclusions` drive the eligibility checker, so review each rule with a subject expert.
3. Set `"data_status"` to a verified value and update the labels shown in the UI.

## Deployment (Vercel + Render)

- **Backend (Render)**: root `backend/`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `GEMINI_API_KEY` and `ALLOWED_ORIGINS=https://<your-frontend>.vercel.app`. Render's default Python image has no Tesseract; use a Docker deploy that installs `tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar`, or accept that image OCR will report "not available". Use a persistent disk or PostgreSQL, because SQLite on ephemeral storage is wiped on redeploy.
- **Frontend (Vercel)**: root `frontend/`, build `npm run build`, output `dist`. Set `VITE_API_BASE=https://<your-backend>.onrender.com`. Add a rewrite of all routes to `/index.html` for client-side routing.

## Known limits of this MVP

- Supabase Auth and PostgreSQL are **not wired in**; history uses SQLite with an anonymous browser id.
- Retrieval is BM25 keyword search (no embeddings). Hindi/Marathi questions rely on Gemini translating the query to English; offline mode only matches the keywords listed in the data.
- Only English, Hindi and Marathi are enabled. To add a language, add it to `LANGUAGES` in `config.py`, add UI strings in `frontend/src/lib/i18n.js` and add eligibility question labels in `eligibility.py`.
- Phase 3 items (automatic portal updates, regional scheme databases, application checklists) are not built.
