# RAG QA Assistant

A full-stack Retrieval-Augmented Generation (RAG) application that answers questions about your PDFs, grounded strictly in their content. Upload a document, ask a question, and get a source-cited answer instead of a hallucinated one.

<img width="1129" height="665" alt="RAG_QA_Screenshot" src="https://github.com/user-attachments/assets/55764538-1aa4-460d-a7c3-6b9efabb8872" />

![Status](https://img.shields.io/badge/status-MVP-green) ![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Features

- PDF ingestion pipeline that extracts, cleans, and chunks PDFs with section-aware metadata
- Semantic search using sentence-transformer embeddings stored in a FAISS vector index
- Claude-powered answers with strict source-grounding, citations, and an "I don't know" fallback to prevent hallucination
- Smart query classification (hybrid rule and LLM classifier) across lookup, how-to, policy, explanation, and data categories
- Data redirect that short-circuits aggregation questions (counts, rates, totals) toward analytics tools instead of forcing retrieval
- Comparison mode that asks one question and shows how two documents answer it differently
- Side-by-side PDF viewer to read source documents alongside the chat
- Confidence scoring derived from retrieval similarity scores
- Markdown export of the full conversation, including all source citations

## Architecture

```
+-------------------------------------------------------------+
|                  React + TypeScript SPA                     |
|                (Vite + Tailwind CSS, port 5173)             |
+--------------------------+----------------------------------+
                           | HTTP / JSON
                           v
+-------------------------------------------------------------+
|                    FastAPI Backend                          |
|                       (port 8000)                           |
+-------------------------------------------------------------+
|  Ingestion  |  Embeddings  |   Query Pipeline               |
|  ---------  |  ----------  |   ---------------              |
|  extractor  |   FAISS      |   classifier > retriever >     |
|  cleaner    |   index      |   generator (Claude)           |
|  chunker    |              |                                |
+-------------------------------------------------------------+
                           |
                           v
                  +------------------+
                  |  Anthropic API   |
                  |  (Claude Haiku)  |
                  +------------------+
```

### How it works

1. **Upload.** A PDF is extracted with `pdfplumber`, cleaned, and chunked into 300 to 800 token segments with section detection and content-type tagging.
2. **Index.** Each chunk is embedded with `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional vectors) and stored in a FAISS `IndexFlatIP` for cosine similarity over normalized vectors.
3. **Classify.** Incoming queries are tagged via a hybrid regex and Claude classifier into one of five categories: `lookup`, `explanation`, `how_to`, `policy`, or `data`.
4. **Route.** Data queries (counts, rates, totals) are redirected to analytics tools because RAG cannot reliably answer aggregation questions over chunked text.
5. **Retrieve.** For all other query types, the top-k most similar chunks are fetched with diversity filtering across sections to avoid redundant context.
6. **Generate.** Claude receives the retrieved chunks plus a type-specific system prompt that enforces source citations and an "I don't know" response when context is insufficient.

## Tech Stack

**Backend**
- Python 3.10+
- FastAPI for the REST API
- FAISS for vector similarity search
- sentence-transformers for local embedding generation
- Anthropic Claude API for answer generation and classification fallback
- pdfplumber, tiktoken, and Pydantic

**Frontend**
- React 18 with TypeScript
- Vite as the dev server and bundler
- Tailwind CSS for utility-first styling

## Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 20 or higher with npm
- An Anthropic API key (available at [console.anthropic.com](https://console.anthropic.com/))

### 1. Clone and configure

```bash
git clone https://github.com/Arman-Pakravan/RAG-QA-Assistant.git
cd RAG-QA-Assistant
cp .env.example .env
```

Then open `.env` and paste your `ANTHROPIC_API_KEY`.

### 2. Backend (FastAPI)

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS or Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend will run at `http://localhost:8000`. Interactive Swagger docs are available at `http://localhost:8000/docs`.

### 3. Frontend (React)

In a second terminal:

```bash
cd frontend-react
npm install
npm run dev
```

The frontend opens at `http://localhost:5173`.

## Project Structure

```
rag-qa-assistant/
|-- app/                       # FastAPI backend
|   |-- api/routes.py          # REST endpoints
|   |-- ingestion/             # PDF to text to chunks
|   |-- embeddings/store.py    # FAISS vector store
|   |-- query/                 # Classifier, retriever, generator
|   |-- config.py
|   `-- main.py
|-- frontend-react/            # React + TypeScript SPA
|   `-- src/
|       |-- api/client.ts      # API client
|       |-- components/        # UI components
|       |-- utils/export.ts    # Markdown export
|       |-- types.ts
|       `-- App.tsx
|-- data/
|   |-- uploads/               # Indexed PDFs (gitignored)
|   `-- index/                 # FAISS index files (gitignored)
|-- requirements.txt
`-- .env.example
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a PDF; extracts, chunks, embeds, and indexes it |
| POST | `/ask` | Ask a grounded question; returns answer with sources and confidence |
| POST | `/compare` | Compare how two documents address a question |
| GET  | `/search` | Top-k retrieval test (no LLM call) |
| GET  | `/classify` | Classify a query without retrieving or answering |
| GET  | `/documents` | List indexed documents |
| GET  | `/documents/{filename}` | Stream a PDF for inline viewing |
| GET  | `/stats` | Index stats including chunk count and indexed documents |
| POST | `/reset` | Wipe the entire index |

Interactive documentation is available at `http://localhost:8000/docs`.

## Example Queries

After indexing a document, try queries like:

- *"What are the key skills listed?"* classified as **Lookup**
- *"How do I reset my password?"* classified as **How-To**
- *"What is the policy on remote work?"* classified as **Policy**
- *"Why does the system use encryption?"* classified as **Explanation**
- *"How many users signed up last quarter?"* classified as **Data** (redirected, not answerable from documents)

## Future Work

- Click-to-jump-to-source page in the PDF viewer
- Conversation memory for multi-turn follow-ups
- OCR fallback for scanned PDFs
- Per-document chunking previews

## License

MIT
