#  What is this?

AI Tutor is a full-stack, production-deployed AI study assistant that transforms your personal notes into an interactive learning experience. Unlike generic chatbots, it's designed to **teach**, not just answer — using the Socratic method to guide students step-by-step through complex concepts.

Built entirely from first principles — no LangChain, no LlamaIndex — every component of the RAG pipeline was engineered manually to demonstrate real system design thinking.

---

##  Features

| Feature | Description |
|---|---|
| **User Auth** | Secure registration & login with PBKDF2-SHA256 password hashing + random salt |
| **Document Ingestion** | Upload PDF, DOCX, or TXT files — parsed via `unstructured` into semantic chunks |
| **Vector Search** | Chunks are embedded with `sentence-transformers` and stored in Milvus Lite |
| **Cross-Encoder Reranking** | Initial results are reranked using a cross-encoder for higher answer accuracy |
| **Socratic Tutor Chat** | Mistral AI responds with structured, step-by-step explanations using Markdown |
| **AI Quiz Generator** | Generates structured MCQ quizzes from your notes in raw JSON format |
| **Progress Dashboard** | Tracks quiz scores, calculates average, and identifies weak topics over time |
| **Weak Area Detection** | Algorithmically flags topics where the user consistently underperforms |

---

##  Architecture

```
User Browser
     │
     ▼
FastAPI Backend (app/)
     │
     ├── /api/upload   →  Unstructured Parser → Sentence-Transformers → Milvus Lite
     │
     ├── /api/chat/tutor →  Milvus Search → Cross-Encoder Reranker → Mistral AI (Socratic Prompt)
     │
     ├── /api/quiz      →  Milvus Search → Mistral AI (JSON-forced prompt)
     │
     ├── /api/quiz/submit →  SQLite (QuizScore table) + Weakness Severity Calculation
     │
     ├── /api/progress  →  SQLite (aggregated scores + weaknesses per user)
     │
     └── /api/auth/*    →  User table (PBKDF2 password hash, session token)
```

**Storage:**
- **Milvus Lite** (`milvus_demo.db`) — Vector database for semantic document search
- **SQLite** (`tutor_progress.db`) — Relational database for users, quiz scores, progress

---

##  Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Uvicorn, SQLAlchemy |
| **AI / LLM** | Mistral AI (`open-mistral-7b`) |
| **Embeddings** | `sentence-transformers` (all-MiniLM-L6-v2) |
| **Vector DB** | Milvus Lite (serverless, no Docker needed) |
| **Reranker** | Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) |
| **Doc Parsing** | `unstructured[all-docs]` |
| **Auth** | PBKDF2-HMAC-SHA256 (Python `hashlib`, no extra deps) |
| **Frontend** | Vanilla HTML/CSS/JS + Chart.js + Marked.js |
| **Deployment** | Docker → Hugging Face Spaces (16GB RAM) |

---

## Running Locally

### Prerequisites
- Python 3.11+
- A free [Mistral AI API key](https://console.mistral.ai/)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Prarabdha14/Ai-Tutor
cd Ai-Tutor

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
echo "MISTRAL_API_KEY=your_key_here" > .env

# 5. Run the app
uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000`

---


---

##  Security Design

- Passwords are **never stored in plaintext**
- Each password is hashed using `hashlib.pbkdf2_hmac("sha256", ...)` with a unique random **16-byte salt** per user
- Session tokens are cryptographically random 8-character hex strings (`secrets.token_hex(4)`)
- API keys are injected via environment variables / HF Secrets — never hardcoded

---

##  Screenshots

> *Live at: [Your Deployment URL will go here]*

-  Login / Register Screen
-  Socratic Tutor Chat with Markdown rendering
-  Interactive MCQ Quiz with instant feedback
-  Progress Dashboard with score chart and weak area detection

---

##  Author

**Roshnik** (GitHub: [@Roshnik26](https://github.com/Roshnik26))
- Deployed live on Hugging Face Spaces / Render

---

<div align="center">
<i>Built from first principles — no LangChain, no shortcuts.</i>
</div>
