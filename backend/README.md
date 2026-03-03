## Backend setup

1. Create a Python virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Configure environment variables in a `.env` file in `backend/app` or project root:

```bash
DATABASE_URL=postgresql+psycopg2://user:password@host/dbname
JWT_SECRET_KEY=your-secret-key
PRIMARY_AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-hf-key
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PROVIDER=pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=enterprise-rag
PINECONE_REGION=us-east-1
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=5
```

3. Ensure the pgvector extension is installed on the PostgreSQL database when using the Postgres vector store.

4. Run the backend:

```bash
uvicorn app.main:app --reload
```

