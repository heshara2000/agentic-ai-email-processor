                Email
                  │
                  ▼
          Email Listener
                  │
                  ▼
        Download Attachment
                  │
                  ▼
        Document Extraction
          (OpenAI / LLM)
                  │
                  ▼
          Structured JSON
                  │
                  ▼
             RAG Search
      (Policies + Managers +
        Departments Store)
                  │
                  ▼
         Validation Result
                  │
         ┌────────┴─────────┐
         │                  │
         ▼                  ▼
 High Confidence      Low Confidence
         │                  │
         ▼                  ▼
 Save to CSV         Human Review CSV



### folder structure

agentic-ai-email-processor/

│
├── app.py
├── graph.py
├── nodes.py
├── state.py
├── prompts.py
├── schemas.py
├── config.py
├── requirements.txt
├── .env
│
├── uploads/
├── chroma_db/
├── knowledge_base/
├── outputs/
├── sample_files/
│
└── README.md