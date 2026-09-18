# AI Security Analytics — Frontend Dashboard

A modern, responsive React + TypeScript dashboard for security analysts and SOC teams. Visualizes real-time phishing and social engineering telemetry using Recharts and provides interactive message analysis.

---

## 1. Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS (Cybersecurity Dark Palette)
- **Charts**: Recharts (Pie, Bar, Horizontal Bar)
- **Icons**: Lucide React
- **API Client**: Native Fetch REST client strictly typed against backend Pydantic schemas

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── api/
│   │   └── client.ts            # Centralized API client targeting backend
│   ├── components/
│   │   ├── KPICard.tsx          # Key performance metric card with variants
│   │   ├── RiskBadge.tsx        # Color-coded severity badge (Critical..Safe)
│   │   ├── ConversationCard.tsx # Detailed conversation view with indicators
│   │   ├── Navbar.tsx           # Navigation header with live API health status
│   │   └── charts/
│   │       ├── CategoryPieChart.tsx # Message classifications (Phishing, Spam, etc.)
│   │       ├── RiskBarChart.tsx     # Severity distribution
│   │       ├── ThreatTypeChart.tsx  # Attack vector distribution
│   │       └── SentimentChart.tsx   # Urgency & psychological manipulation index
│   ├── hooks/
│   │   └── useApi.ts            # Generic API fetch/state management hook
│   ├── pages/
│   │   ├── Dashboard.tsx        # KPI metrics & 4 visualization charts
│   │   ├── Analyze.tsx          # Submission form with 1-click test presets
│   │   └── Conversations.tsx    # Paginated history with risk filter & search
│   ├── types/
│   │   └── analysis.ts          # Locked schema and domain TypeScript interfaces
│   ├── App.tsx                  # Main layout and tab orchestrator
│   ├── main.tsx                 # Entrypoint
│   ├── index.css                # Global styles & custom scrollbars
│   └── vite-env.d.ts            # Environment typing
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── .env.example
└── README.md
```

---

## 3. Local Setup & Running

### Prerequisites
- Node.js v18+ (v20+ recommended)
- npm v9+

### Quickstart
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment variables
cp .env.example .env

# 4. Start Vite development server
npm run dev
```

The frontend will be available at: [http://localhost:5173](http://localhost:5173).

---

## 4. Environment Variables

In `.env`:
```env
# URL where FastAPI backend is listening
VITE_API_BASE_URL=http://localhost:8000
```

> **Security Note**: Never add `GEMINI_API_KEY` to frontend environment variables. All AI reasoning and keys reside strictly within the backend service layer.

---

## 5. Features & Pages

### 1. Dashboard (`/`)
- **KPI Metrics**: Total Communications, High-Risk Alerts, Pending Triage, Resolved Cases.
- **Visualizations**:
  - *Risk Level Distribution* (Critical, High, Medium, Low, Safe)
  - *Message Classifications* (Phishing, Malicious, Spam, Clean)
  - *Detected Threat Signatures* (Credential Harvesting, Financial Fraud, Social Engineering)
  - *Sentiment & Urgency Index* (Urgent, Alarming, Negative, Neutral, Positive)

### 2. Analyze Page (`/analyze`)
- Submit sender, subject, message body, and URLs.
- **1-Click Test Presets**:
  - `Credential Phishing (IP URL)`
  - `Brand Spoofing (Free-mail)`
  - `Clean Business Meeting`
- Full breakdown of the 11-field Locked Schema with actionable remediation recommendations.

### 3. Conversations Page (`/conversations`)
- Paginated table/card view of all previously evaluated communications.
- Filter by Risk Level (`Critical`, `High`, `Medium`, `Low`, `Safe`).
- Client-side search by sender, subject, or message content.
- Expandable detail view revealing full headers, extracted URLs, and detected security rule indicators.
