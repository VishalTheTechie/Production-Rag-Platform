# RAG Platform
Phase 1: baseline RAG with access-control metadata on every chunk.

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your Gemini key
3. `docker compose up -d`
4. `python generate_docs.py` then `python ingest.py`
5. `uvicorn main:app --reload` and open http://localhost:8000/docs
6. `python make_eval_set.py` then `python run_eval.py baseline`
