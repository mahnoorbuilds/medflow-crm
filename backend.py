# ═══════════════════════════════════════════════
# MedFlow CRM — FastAPI Backend
# ═══════════════════════════════════════════════

# Step1: Import Database objects
from database import init_db, Appointment, get_db
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tables should be initialized once via a script, not on every serverless invocation!
# init_db()

# Step3: Create Data Contracts using Pydantic Models
import datetime as dt
from pydantic import BaseModel

class AppointmentRequest(BaseModel):
    patient_name: str
    reason: str
    start_time: dt.datetime

class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    reason: str | None
    start_time: dt.datetime
    canceled: bool
    created_at: dt.datetime

class CancelAppointmentRequest(BaseModel):
    patient_name: str
    date: dt.date

class CancelAppointmentResponse(BaseModel):
    canceled_count: int

class ListAppointmentRequest(BaseModel):
    date: dt.date

# Step2: Create FastAPI application and endpoints

from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func


app = FastAPI(title="MedFlow CRM — Hospital Appointment System")

# CORS middleware — allows VAPI and other services to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Files ──────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve index.html at root
@app.get("/")
async def serve_root():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ─── Original Endpoints (Streamlit compatible) ─

# schedule appt
@app.post("/schedule_appointment/")
def schedule_appointment(request: AppointmentRequest, db: Session = Depends(get_db)):
    new_appointment = Appointment(
            patient_name=request.patient_name,
            reason=request.reason,
            start_time=request.start_time,
        )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    new_appointment_return_obj = AppointmentResponse(
        id = new_appointment.id,
        patient_name= new_appointment.patient_name,
        reason=new_appointment.reason,
        start_time=new_appointment.start_time,
        canceled=new_appointment.canceled,
        created_at=new_appointment.created_at
    )
    return new_appointment_return_obj


# cancel appt
@app.post("/cancel_appointment/")
def cancel_appointment(request: CancelAppointmentRequest, db: Session = Depends(get_db)):   
    
    start_dt = dt.datetime.combine(request.date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)

    result = db.execute(
        select(Appointment)
        .where(Appointment.patient_name == request.patient_name)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time < end_dt)
        .where(Appointment.canceled == False)
    )

    appointments = result.scalars().all()
    if not appointments:
        return CancelAppointmentResponse(canceled_count=0)

    for appointment in appointments:
        appointment.canceled = True
    
    db.commit()
    
    return CancelAppointmentResponse(canceled_count=len(appointments))

# list appt
@app.post("/list_appointments/")
def list_appointments(request: ListAppointmentRequest, db: Session = Depends(get_db)):
    
    start_dt = dt.datetime.combine(request.date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)
    
    result = db.execute(
        select(Appointment)
        .where(Appointment.canceled == False)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time < end_dt)
        .order_by(Appointment.start_time.asc())
    )
    booked_appointments = []
    for appointment in result.scalars().all():
        appointment_obj = AppointmentResponse(
        id=appointment.id,
        patient_name=appointment.patient_name,
        reason=appointment.reason,
        start_time=appointment.start_time,
        canceled=appointment.canceled,
        created_at=appointment.created_at
    )
        booked_appointments.append(appointment_obj)

    return booked_appointments


# ─── Dashboard API Endpoints ───────────────────

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard stats: total, today, upcoming, canceled."""
    today_start = dt.datetime.combine(dt.date.today(), dt.time.min)
    today_end = today_start + dt.timedelta(days=1)
    now = dt.datetime.utcnow()

    total = db.query(func.count(Appointment.id)).scalar() or 0

    today_count = db.query(func.count(Appointment.id)).filter(
        Appointment.start_time >= today_start,
        Appointment.start_time < today_end,
        Appointment.canceled == False,
    ).scalar() or 0

    upcoming = db.query(func.count(Appointment.id)).filter(
        Appointment.start_time >= now,
        Appointment.canceled == False,
    ).scalar() or 0

    canceled = db.query(func.count(Appointment.id)).filter(
        Appointment.canceled == True,
    ).scalar() or 0

    return {
        "total": total,
        "today": today_count,
        "upcoming": upcoming,
        "canceled": canceled,
    }


@app.get("/api/init")
def init_tables():
    from database import init_db
    init_db()
    return {"status": "ok", "message": "Tables created."}

@app.get("/api/appointments")
def get_appointments(
    date: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List appointments with optional date and status filters."""
    query = select(Appointment).order_by(Appointment.start_time.desc())

    if date:
        date_obj = dt.date.fromisoformat(date)
        start_dt = dt.datetime.combine(date_obj, dt.time.min)
        end_dt = start_dt + dt.timedelta(days=1)
        query = query.where(Appointment.start_time >= start_dt).where(Appointment.start_time < end_dt)

    if status == "active":
        query = query.where(Appointment.canceled == False)
    elif status == "canceled":
        query = query.where(Appointment.canceled == True)

    result = db.execute(query)
    appointments = result.scalars().all()

    return [
        {
            "id": a.id,
            "patient_name": a.patient_name,
            "reason": a.reason,
            "start_time": a.start_time.isoformat(),
            "canceled": a.canceled,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in appointments
    ]


@app.get("/api/appointments/search")
def search_appointments(
    name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Search appointments by patient name."""
    result = db.execute(
        select(Appointment)
        .where(Appointment.patient_name.ilike(f"%{name}%"))
        .order_by(Appointment.start_time.desc())
        .limit(50)
    )
    appointments = result.scalars().all()

    return [
        {
            "id": a.id,
            "patient_name": a.patient_name,
            "reason": a.reason,
            "start_time": a.start_time.isoformat(),
            "canceled": a.canceled,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in appointments
    ]


# ─── VAPI Webhook Endpoint ─────────────────────

@app.get("/vapi/webhook")
async def vapi_webhook_get():
    """Friendly response for users checking the webhook URL in their browser."""
    return {"status": "Webhook is active. Please configure VAPI to send POST requests to this URL."}

@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Single endpoint for VAPI server URL.
    Handles tool-calls, status-update, and end-of-call-report messages.
    """
    body = await request.json()
    message = body.get("message", {})
    msg_type = message.get("type", "")

    logger.info(f"VAPI webhook received: type={msg_type}")

    # ── tool-calls: dispatch to the right handler ──
    if msg_type == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []

        db = next(get_db())
        try:
            for tc in tool_calls:
                tool_call_id = tc.get("id", "")
                func = tc.get("function", {})
                func_name = func.get("name", "")
                raw_args = func.get("arguments", "{}")

                # arguments can be a string or dict
                try:
                    if isinstance(raw_args, str):
                        args = json.loads(raw_args)
                    else:
                        args = raw_args
                except json.JSONDecodeError:
                    logger.error(f"  Error decoding JSON arguments: {raw_args}")
                    results.append({"toolCallId": tool_call_id, "result": "Error: Invalid JSON in arguments"})
                    continue

                logger.info(f"  Tool call: {func_name} | args={args}")

                try:
                    result_text = _dispatch_tool(func_name, args, db)
                except Exception as exc:
                    logger.error(f"  Error in {func_name}: {exc}")
                    result_text = f"Error: {exc}"

                results.append({"toolCallId": tool_call_id, "result": result_text})
        finally:
            db.close()

        return {"results": results}
    else:
        logger.warning(f"Unknown message type: {msg_type} | body={body}")
        return {"status": "ignored"}

# ─── Direct Custom Tool Endpoints ───────────────

@app.post("/api/schedule_appointment")
async def api_schedule_appointment(request: Request):
    """Direct REST endpoint for VAPI Custom Tool."""
    db = next(get_db())
    try:
        args = await request.json()
        logger.info(f"Direct tool call schedule_appointment | args={args}")
        result_text = _dispatch_tool("schedule_appointment", args, db)
        return {"result": result_text}
    except Exception as exc:
        logger.error(f"Error in api_schedule_appointment: {exc}")
        return {"result": f"Error: {exc}"}
    finally:
        db.close()

@app.post("/api/list_appointments")
async def api_list_appointments(request: Request):
    """Direct REST endpoint for VAPI Custom Tool."""
    db = next(get_db())
    try:
        args = await request.json()
        logger.info(f"Direct tool call list_appointments | args={args}")
        result_text = _dispatch_tool("list_appointments", args, db)
        return {"result": result_text}
    except Exception as exc:
        logger.error(f"Error in api_list_appointments: {exc}")
        return {"result": f"Error: {exc}"}
    finally:
        db.close()

@app.post("/api/check_availability")
async def api_check_availability(request: Request):
    """Alias for list_appointments to check availability."""
    db = next(get_db())
    try:
        args = await request.json()
        logger.info(f"Direct tool call check_availability | args={args}")
        result_text = _dispatch_tool("list_appointments", args, db)
        return {"result": result_text}
    except Exception as exc:
        logger.error(f"Error in api_check_availability: {exc}")
        return {"result": f"Error: {exc}"}
    finally:
        db.close()


def _dispatch_tool(func_name: str, args: dict, db: Session) -> str:
    """Route a VAPI tool call to the matching business logic."""

    if func_name == "schedule_appointment":
        new_appt = Appointment(
            patient_name=args["patient_name"],
            reason=args.get("reason", ""),
            start_time=dt.datetime.fromisoformat(args["start_time"]),
        )
        db.add(new_appt)
        db.commit()
        db.refresh(new_appt)
        return (
            f"Appointment scheduled successfully for {new_appt.patient_name} "
            f"on {new_appt.start_time.strftime('%B %d, %Y at %I:%M %p')}. "
            f"Appointment ID is {new_appt.id}."
        )

    elif func_name == "cancel_appointment":
        date_obj = dt.date.fromisoformat(args["date"])
        start_dt = dt.datetime.combine(date_obj, dt.time.min)
        end_dt = start_dt + dt.timedelta(days=1)

        result = db.execute(
            select(Appointment)
            .where(Appointment.patient_name == args["patient_name"])
            .where(Appointment.start_time >= start_dt)
            .where(Appointment.start_time < end_dt)
            .where(Appointment.canceled == False)
        )
        appointments = result.scalars().all()

        if not appointments:
            return f"No active appointments found for {args['patient_name']} on {args['date']}."

        for appt in appointments:
            appt.canceled = True
        db.commit()
        return f"Successfully canceled {len(appointments)} appointment(s) for {args['patient_name']} on {args['date']}."

    elif func_name == "list_appointments":
        date_obj = dt.date.fromisoformat(args["date"])
        start_dt = dt.datetime.combine(date_obj, dt.time.min)
        end_dt = start_dt + dt.timedelta(days=1)

        result = db.execute(
            select(Appointment)
            .where(Appointment.canceled == False)
            .where(Appointment.start_time >= start_dt)
            .where(Appointment.start_time < end_dt)
            .order_by(Appointment.start_time.asc())
        )
        appts = result.scalars().all()

        if not appts:
            return f"No appointments scheduled for {args['date']}."

        lines = [f"Appointments for {args['date']}:"]
        for a in appts:
            lines.append(
                f"  - {a.patient_name} at {a.start_time.strftime('%I:%M %p')}"
                f" (Reason: {a.reason or 'N/A'}, ID: {a.id})"
            )
        return "\n".join(lines)

    else:
        return f"Unknown function: {func_name}"


# ─── Server Entry Point ───────────────────────

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4444))
    uvicorn.run("backend:app", host="0.0.0.0", port=port, reload=True)
