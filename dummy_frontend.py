# Step5: Streamlit dashboard (Just for testing)
import streamlit as st
import datetime as dt
import requests

st.title("Dubai Hospital Appointment Booking Portal")
base_url = st.text_input("Backend URL", "http://localhost:4444").rstrip("/")

patient_name = st.text_input("Patient name")
reason = st.text_input("Reason")
start_date = st.date_input("Date", value=dt.date.today() + dt.timedelta(days=1))
start_time = st.time_input("Time", value=dt.time(9, 0))

if st.button("Schedule"):
    start_dt = dt.datetime.combine(start_date, start_time)
    payload = {
        "patient_name": patient_name.strip(),
        "reason": reason.strip() or None,
        "start_time": start_dt.isoformat(),
    }
    try:
        resp = requests.post(f"{base_url}/schedule_appointment/", json=payload, timeout=10)
        resp.raise_for_status()
        st.success("Scheduled")
    except requests.RequestException as exc:
        st.error(f"Schedule failed: {exc}")

st.divider()
st.subheader("Cancel")

cancel_name = st.text_input("Patient name to cancel", key="cancel_name")
cancel_date = st.date_input("Date to cancel", key="cancel_date", value=dt.date.today())

if st.button("Cancel appointments"):
    payload = {
            "patient_name": cancel_name.strip(), 
            "date": cancel_date.isoformat()
               }
    try:
        resp = requests.post(f"{base_url}/cancel_appointment/", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        st.success(f"Canceled: {data.get('canceled_count', 0)}")    
    except requests.HTTPError:
        st.error(resp.text)
    except requests.RequestException as exc:
        st.error(f"Cancel failed: {exc}")


appointments_date = st.date_input("Date to check appointments", key="check_appointment_date", value=dt.date.today())
if st.button("Check appointments"):
    try:
        params = {"date": appointments_date.isoformat()}
        resp = requests.post(f"{base_url}/list_appointments/", params=params, timeout=10)
        resp.raise_for_status()
        st.dataframe(resp.json(), use_container_width=True, hide_index=True)
    except requests.RequestException as exc:
        st.warning(f"Could not load appointments: {exc}")