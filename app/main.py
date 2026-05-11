from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(title="RAG QA Assistant", version="0.3.0")

# Allow Streamlit (and any local origin) to fetch PDFs and call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: open. Tighten for production.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "service": "RAG QA Assistant"}


@app.get("/health")
def health():
    return {"status": "healthy"}