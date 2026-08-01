# 🏥 VAPI Voice Agent — Hospital Appointment System

An AI-powered voice agent backend for managing hospital appointments, built with **FastAPI**, **SQLAlchemy**, and **Streamlit**. Designed to integrate with [VAPI](https://vapi.ai/) for conversational voice interactions, enabling patients to schedule, cancel, and list appointments via natural language.

---

## ✨ Features

- **Schedule Appointments** — Book a new appointment with patient name, reason, and preferred time.
- **Cancel Appointments** — Cancel all appointments for a patient on a given date.
- **List Appointments** — View all active (non-canceled) appointments for a specific date.
- **Streamlit Dashboard** — A simple web UI for testing the API endpoints.
- **SQLite Database** — Lightweight, file-based persistence with zero configuration.

---

## 🏗️ Project Structure

```
├── backend.py          # FastAPI server with appointment endpoints
├── database.py         # SQLAlchemy models, engine, and session management
├── dummy_frontend.py   # Streamlit dashboard for testing
├── db_demo.py          # Utility script for raw SQL queries against the DB
├── pyproject.toml      # Project metadata and dependencies
└── README.md
```

---

## 📋 Prerequisites

- **Python 3.11+**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd vapi-voice-agent
```

### 2. Create a virtual environment & install dependencies

Using **uv** (recommended):

```bash
uv venv
source .venv/bin/activate
uv sync
```

Or using **pip**:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi sqlalchemy streamlit uvicorn
```

### 3. Start the backend server

```bash
python backend.py
```

The API will be available at **http://127.0.0.1:4444**.

### 4. (Optional) Launch the Streamlit dashboard

```bash
streamlit run dummy_frontend.py
```

---

## 📡 API Endpoints

All endpoints accept JSON payloads via **POST**.

### Schedule an Appointment

```
POST /schedule_appointment/
```

| Field          | Type     | Description                    |
| -------------- | -------- | ------------------------------ |
| `patient_name` | `string` | Name of the patient            |
| `reason`       | `string` | Reason for the appointment     |
| `start_time`   | `string` | ISO 8601 datetime (e.g. `2026-02-20T09:00:00`) |

**Example:**

```json
{
  "patient_name": "Hassan",
  "reason": "Annual checkup",
  "start_time": "2026-02-20T09:00:00"
}
```

---

### Cancel Appointments

```
POST /cancel_appointment/
```

| Field          | Type     | Description                          |
| -------------- | -------- | ------------------------------------ |
| `patient_name` | `string` | Name of the patient                  |
| `date`         | `string` | Date to cancel appointments for (ISO 8601, e.g. `2026-02-20`) |

---

### List Appointments

```
POST /list_appointments/
```

| Field  | Type     | Description                        |
| ------ | -------- | ---------------------------------- |
| `date` | `string` | Date to list appointments for (ISO 8601, e.g. `2026-02-20`) |

---

## 🗄️ Database

The project uses **SQLite** via SQLAlchemy. The database file (`appointments_db.db`) is created automatically on first run.

### Appointment Schema

| Column         | Type       | Description                 |
| -------------- | ---------- | --------------------------- |
| `id`           | Integer    | Primary key (auto-increment)|
| `patient_name` | String     | Patient's name              |
| `reason`       | String     | Reason for visit (optional) |
| `start_time`   | DateTime   | Appointment date & time     |
| `canceled`     | Boolean    | Cancellation status         |
| `created_at`   | DateTime   | Record creation timestamp   |

### Running raw queries

Use the `db_demo.py` utility to inspect the database directly:

```bash
python db_demo.py
```

---

## 🔌 VAPI Integration

This backend is designed to serve as a tool/function provider for a **VAPI voice agent**. Point your VAPI assistant's server URL to the running backend and configure the three tool functions (`schedule_appointment`, `cancel_appointment`, `list_appointments`) to enable voice-driven appointment management.

---

## 📦 Dependencies

| Package     | Purpose                        |
| ----------- | ------------------------------ |
| FastAPI     | Web framework for the REST API |
| SQLAlchemy  | ORM and database toolkit       |
| Uvicorn     | ASGI server                    |
| Streamlit   | Testing dashboard UI           |

---

## 📄 License

This project is for educational and demonstration purposes.