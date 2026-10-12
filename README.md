# GeoForensics

**GeoForensics AI** is an advanced OSINT forensic intelligence platform that geolocates images without GPS metadata. Combining multimodal vision AI, OpenStreetMap live verification, road infrastructure taxonomy, multilingual OCR, and botanical forensics, it triangulates street-level coordinates with verifiable confidence scoring and directed evidence graphs.

---

## ⚡ Core Architecture

- **Multimodal OSINT Vision**: Powered by Google Gemini with GeoGuessr infrastructure forensics (utility pole taxonomy, kerb markings, driving side, soil hue, vegetation biomes).
- **Spatial Verification Engine**: Multi-tier geocoding ladder via OpenStreetMap Nominatim with strict structured filtering (prioritizing physical settlements and POIs over broad boundary polygons).
- **Forensic Pipeline**:
  - Stage 1: Image Preprocessing
  - Stage 2: EXIF & Hardware Metadata Extraction
  - Stage 3: Multilingual OCR & Script Analysis
  - Stage 4: Visual Scene & Environmental Understanding
  - Stage 5: Road Infrastructure & Marking Detection
  - Stage 6: Architecture Forensic Analysis
  - Stage 7: Landmark & Heritage Matching
  - Stage 8: Gemini Multimodal AI Vision
  - Stage 9: Tampering & Reliability Verification
  - Stage 10: Evidence Graph Construction
  - Stage 11: Bayesian Candidate Scoring & Ranking
  - Stage 12: Exact Physical Coordinate Resolution

---

## 🛠️ Quickstart

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:
```env
GEMINI_API_KEY="your-gemini-api-key"
```

Start the API server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.
