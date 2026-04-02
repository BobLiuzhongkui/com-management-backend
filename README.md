# Com Management Backend
Full-stack communication management platform.

## Tech Stack
- **Frontend**: Next.js + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query + Zustand
- **Backend**: FastAPI + Python + Pydantic + Service/Repository layered architecture

## Project Structure
```
├── frontend/          # Next.js application
│   ├── src/app/       # App Router + pages
│   ├── src/components/
│   ├── src/lib/
│   ├── src/stores/
│   ├── src/services/
│   └── src/types/
└── backend/           # FastAPI application
    └── app/
        ├── api/       # Route endpoints
        ├── core/      # Config, DB setup
        ├── models/    # SQLAlchemy models
        ├── schemas/   # Pydantic schemas
        ├── services/  # Business logic
        ├── repositories/  # Data access
        ├── adapters/  # External integrations (abstract)
        └── utils/     # Helpers
```

## Quick Start
```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```
