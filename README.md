[block911_github_readme.md](https://github.com/user-attachments/files/35467539/block911_github_readme.md)
# 🛡️ Block911 — Real-Time Payment Fraud Intelligence & Syndicate Graph Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![D3.js](https://img.shields.io/badge/D3.js-v7.8-F9A03C.svg)](https://d3js.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC.svg)](https://tailwindcss.com/)

**Block911** is a real-time, pre-settlement payment fraud detection platform and SecOps investigation dashboard. Designed to sit at the **merchant checkout** or **payment gateway webhook** layer, it evaluates transactions in milliseconds using behavioral heuristics, browser telemetry, and connected-component graph analytics to stop organized fraud rings *before* funds are settled.

---

## ✨ Key Features

* **⚡ Real-Time Risk Scoring Engine (`engine.py`):** Evaluates incoming payment payloads against weighted fraud signals (ticket anomalies, VPN/Tor exit nodes, 10-minute velocity bursts, WebGL canvas spoofing, disposable emails, and active blacklists) in `< 50ms`.
* **🕸️ Syndicate Graph Intelligence (`D3.js` + BFS):** Automatically links flagged customers, hardware device fingerprints, card BINs, and IP addresses into an interactive force-directed network graph. Uses Breadth-First Search (BFS) to detect hidden multi-account fraud rings.
* **🛍️ Live Merchant Checkout Collector (`shop.html`):** A realistic demo e-commerce storefront that captures client behavioral signals (timezone mismatches, sub-human form completion speeds, clipboard paste events, and headless browser flags) and streams orders directly to the dashboard via `BroadcastChannel` and REST APIs.
* **🕵️ SecOps Analyst Review Queue:** Interactive triage console allowing investigators to inspect raw JSON telemetry, verify triggered rules, add forensic notes, and resolve cases as **Fraud (Auto-Blacklist)** or **False Positive**.
* **🧪 Payment Test Lab:** Built-in sandbox simulator to test custom transaction scenarios and observe live score calculations before injecting events into the stream.
* **💾 Atomic SQLite Persistence (`database.py`):** Backed by SQLite in Write-Ahead Logging (`WAL`) mode for concurrent, race-free transaction logging and blacklist enforcement.

---

## 🏗️ System Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (static/)                            │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │
│  │  index.html (SecOps HUD)     │  │  shop.html (Demo Checkout)   │  │
│  │  • Live Ledger & Sparkline   │  │  • Cart & Payment Form       │  │
│  │  • D3 Syndicate Network Map  │  │  • Browser Behavioral Signals│  │
│  │  • Review Queue & Test Lab   │  │  • Cross-Tab Sync            │  │
│  └──────────────┬───────────────┘  └──────────────┬───────────────┘  │
└─────────────────┼─────────────────────────────────┼──────────────────┘
                  │         REST API (JSON)         │
                  ▼                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     BACKEND API (FastAPI - main.py)                  │
│  • Input Validation (Pydantic)                                       │
│  • BFS Connected-Component Ring Detection                            │
│  • Graph Node/Edge Upsert & Blacklist Enforcement                    │
└─────────────────┬─────────────────────────────────┬──────────────────┘
                  │                                 │
                  ▼                                 ▼
┌──────────────────────────────────┐  ┌────────────────────────────────┐
│   SCORING ENGINE (engine.py)     │  │   PERSISTENCE (database.py)    │
│   • Pure Python Rule Matrix      │  │   • SQLite (block911.db - WAL) │
│   • Clamped Score (8 – 98)       │  │   • transactions, blacklist,   │
│   • Cutoffs: <30 Safe, >=75 Deny │  │     graph_nodes, graph_edges   │
└──────────────────────────────────┘  └────────────────────────────────┘
```

---

## 🧮 Fraud Scoring Logic & Thresholds

Every transaction starts with a neutral baseline of **15 points**, accumulates penalties for triggered risk signals, and is clamped between **8 and 98**:

$$\text{Risk Score} = \min\Big(98,\ \max\big(8,\ 15 + \sum \text{Triggered Rule Penalties}\big)\Big)$$

| Signal / Heuristic Rule | Penalty | Trigger Condition |
| :--- | :---: | :--- |
| **Baseline Score** | `+15` | Default starting risk for every initiated payment |
| **High Ticket Value** | `+22` | Transaction amount exceeds threshold (`> $1,000` / high baseline) |
| **Tor / Datacenter Proxy** | `+35` | `proxy_detected == True` or known VPN/Tor exit IP |
| **High 10m Velocity** | `+24` | More than 4 attempts within 10 minutes (`velocity_10m > 4`) |
| **Device Spoofing** | `+20` | `device_spoofed == True` (UserAgent / WebGL canvas mismatch) |
| **Disposable Email** | `+12` | Burner email domains (`tempmail.com`, `mailinator.com`, `yopmail.com`, etc.) |
| **Blacklisted Identity** | `+40` | Customer email exists in the confirmed fraud `blacklist` table |
| **Behavioral Telemetry** | `+6 to +18` | Timezone mismatch (`+18`), bot fill speed `< 2.5s` (`+15`), pasted details (`+6`) |

### Decision Cutoffs
* **`Score < 30` → Approved (`Safe`):** Frictionless checkout; no user interruption.
* **`30 ≤ Score < 75` → Challenged (`3DS OTP Pending`):** Triggers step-up OTP/biometric verification and queues for review.
* **`Score ≥ 75` → Declined (`Open Triage`):** Blocked prior to settlement; entities added to the syndicate graph.

---

## 📂 Project Structure

```text
Block911/
├── database.py          # SQLite schema, WAL connection manager & initial seed data
├── engine.py            # Stateless Python fraud scoring rules & decision thresholds
├── main.py              # FastAPI REST endpoints, BFS ring detection & static server
├── requirements.txt     # Python dependencies (fastapi, uvicorn, httpx)
├── test_api.py          # Automated end-to-end API & scoring test suite
└── static/
    ├── index.html       # Main SecOps fraud monitoring & graph investigation dashboard
    └── shop.html        # Simulated e-commerce checkout for live telemetry testing
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/block911.git
cd block911
```

### 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Automated Test Suite
Verify that the database schema, scoring weights, blacklisting, and graph updates pass all checks:
```bash
python test_api.py
```

### 4. Start the FastAPI Server
```bash
uvicorn main:app --reload
```

### 5. Access the Application
* **Main Fraud Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Demo Online Store:** [http://127.0.0.1:8000/static/shop.html](http://127.0.0.1:8000/static/shop.html)
* **Interactive API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

> **Tip:** To reset the database back to the initial seed transactions and graph nodes, stop the server, delete `block911.db`, and restart `uvicorn`.

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Check backend API availability |
| `GET` | `/api/config` | Retrieve active score cutoffs and disposable domain list |
| `GET` | `/api/transactions?status=&q=` | Fetch transaction ledger with optional status and search filters |
| `POST` | `/api/transactions` | Score, store, and graph-index a new payment payload |
| `POST` | `/api/transactions/{id}/resolve` | Submit analyst verdict (`Fraud` or `Safe`) and optional notes |
| `GET` | `/api/graph` | Return graph nodes, edges, and detected BFS fraud rings |
| `GET` | `/api/stats` | Fetch KPI metrics (total volume, blocked count, active rings) |
| `GET` | `/api/blacklist` | List all blacklisted customer email addresses |

---

## 🔮 Future Roadmap

* **Machine Learning Integration:** Plug an `XGBoost` or `Isolation Forest` anomaly classifier alongside `engine.py` for hybrid heuristic + ML scoring.
* **Distributed Caching:** Migrate velocity counters and blacklist lookups to **Redis** for sub-millisecond high-concurrency throughput.
* **Payment Gateway Webhooks:** Native HMAC-verified webhook adapters for **Razorpay**, **Cashfree**, and **Stripe**.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
