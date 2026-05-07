# Nirṇay (निर्णय) — AI-Powered Procurement Intelligence

Nirṇay is an AI-powered procurement intelligence platform that transforms government tender evaluation from a slow, inconsistent, manual process into an auditable, explainable, and fraud-aware workflow.

Built for high-stakes contexts (e.g., CRPF procurement), Nirṇay ingests tender documents and bidder submissions in any format—typed PDFs, scanned certificates, photographs, or Word files—and produces criterion-level verdicts with full source traceability.

## Key Features

- **Multi-Format Ingestion:** Handles scanned PDFs, images (via OCR), and Word documents.
- **Credibility Intelligence:**
  - **Authenticity Scoring:** Scores document reliability.
  - **Anomaly Detection:** Detects cross-bidder collusion signals, recycled documents, and shared entities.
  - **Contradiction Checking:** Identifies internal inconsistencies in tenders before evaluation.
- **Explainable Verdicts:** Every eligibility decision is backed by a specific reason and source citation.
- **Human-in-the-Loop:** Flagging ambiguous cases for manual review with detailed reasoning.
- **Full Audit Trail:** Logs every officer action and LLM decision for transparency.

## Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Intelligence:** Groq (Llama 3.3 70B Versatile) for high-accuracy reasoning.
- **OCR/Extraction:** Tesseract, PDFMiner, PyMuPDF.
- **Database:** SQLAlchemy with SQLite (default) or PostgreSQL.
- **Analysis:** Scikit-learn, NetworkX (for relationship/anomaly mapping).

### Frontend
- **Framework:** React 18 with TypeScript and Vite.
- **Styling:** Tailwind CSS.
- **Visualization:** React Force Graph (for relationship mapping).
- **Auth:** Firebase Authentication.

##  Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Tesseract OCR (`apt-get install tesseract-ocr`)
- [Groq API Key](https://console.groq.com)
- [Firebase Project](https://console.firebase.google.com) (for Authentication)

---

### Method 1: Docker (Recommended)
1. **Clone the repository**
2. **Configure Environment Variables:**
   - Create a `.env` file in the root directory (using `.env.example` as a template).
   - Set `GROQ_API_KEY` and `FIREBASE_PROJECT_ID`.
3. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```
4. Access the app:
   - Frontend: `http://localhost`
   - Backend API: `http://localhost:8080`

---

### Method 2: Manual Local Setup

#### 1. Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install groq  # Ensure Groq client is installed
   ```
3. Configure `.env`:
   ```bash
   cp .env.example .env
   # Fill in GROQ_API_KEY, FIREBASE_PROJECT_ID, etc.
   ```
4. Start the server:
   ```bash
   uvicorn main:app --reload --port 8080
   ```

#### 2. Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure `.env`:
   ```bash
   cp .env.example .env.local
   # Set VITE_API_BASE_URL=http://localhost:8080
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

##  Project Structure

```text
├── backend/            # FastAPI server, LLM services, and OCR logic
│   ├── db/             # Database models and session management
│   ├── models/         # Pydantic models for API
│   ├── routers/        # API endpoints (ingestion, evaluation, etc.)
│   ├── services/       # Core logic (LLM clients, OCR, anomaly detection)
│   └── tests/          # Backend unit and integration tests
├── frontend/           # React + Vite application
│   ├── src/
│   │   ├── api/        # Axios client and API calls
│   │   ├── components/ # Reusable UI components
│   │   └── pages/      # Application views (Dashboard, Upload, etc.)
└── docker-compose.yml  # Orchestration for containers
```
