# Contributing to GeoForensics AI

Thank you for your interest in contributing to **GeoForensics AI**. This project adheres to high software engineering, security, and scientific forensics standards.

---

## Development Principles

1. **Deterministic Verification over Hallucination**: AI multimodal deductions must be anchored to verifiable physical entities (OpenStreetMap nodes, road registries, or EXIF metadata).
2. **Defensive Security and Privacy**: Never commit API keys, personal images, or location coordinates from private intelligence investigations.
3. **Graceful Degradation**: Every network or multimodal stage must feature offline fallbacks (e.g. offline geospatial DB, rule-based heuristics).
4. **Strong Typing and Schema Integrity**: All backend models must inherit from Pydantic `BaseModel`; all frontend state must be strictly typed in TypeScript.

---

## Setting Up the Development Environment

### Backend (FastAPI + Python 3.11+)
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
cp .env.example .env      # Add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite + TypeScript)
```bash
cd frontend
npm install
npm run dev
```

---

## Code Quality and Testing

Before submitting a Pull Request:
- **Python**: Ensure syntax compiles with `python -m py_compile` across all modified files.
- **TypeScript**: Run `npm run build` or `npx tsc --noEmit` to verify type safety.
- **Git Hygiene**: Follow Conventional Commits format (`feat:`, `fix:`, `refactor:`, `docs:`, `perf:`).

---

## Code of Conduct and Ethical OSINT Use

GeoForensics AI is built for defensive geolocation, humanitarian disaster response, academic research, verification of open-source conflict footage, and anti-misinformation analysis. Do not use this tool for harassment, stalking, or unlawful surveillance.
