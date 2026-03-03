"""
Trifecta AI Agent - Dashboard
===================================
Streamlit dashboard wired to the Trifecta Flask API (via TRIFECTA_API_URL).
Run with: streamlit run test_dashboard_simple.py
"""

import os
from datetime import datetime

import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Configuration
API_BASE_URL = (
    os.getenv("TRIFECTA_API_URL")
    or os.getenv("FLASK_URL")
    or "http://127.0.0.1:5000"
).rstrip("/")
API_KEY = os.getenv("TRIFECTA_API_KEY", "").strip()
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))


# -----------------------------
# Helpers
# -----------------------------

def api_get(path: str, timeout: int = REQUEST_TIMEOUT):
    url = f"{API_BASE_URL}{path}"
    try:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.ok:
            return {"ok": True, "data": res.json()}
        return {"ok": False, "error": f"{res.status_code}: {res.text}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def safe_get(dct, key, default):
    if isinstance(dct, dict) and key in dct:
        return dct[key]
    return default


# -----------------------------
# Page setup
# -----------------------------

st.set_page_config(
    page_title="Trifecta AI Agention Center",
    page_icon="T",
    layout="wide",
)

# Inject CSS (dark teal theme)
st.markdown(
    """
    <style>
      :root {
        --bg: #0b1217;
        --bg2: #0f1b23;
        --panel: #111f28;
        --panel2: #0f1920;
        --accent: #1db3b8;
        --accent2: #0f8f97;
        --text: #e6eef2;
        --muted: #9fb0b7;
        --shadow: rgba(0, 0, 0, 0.35);
        --radius: 16px;
      }

      html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 12% 8%, #132634 0%, var(--bg) 55%) !important;
        color: var(--text) !important;
      }

      .block-container {
        padding-top: 1.2rem;
      }

      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a141b 0%, #0f1b22 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
      }

      [data-testid="stSidebar"] * { color: var(--text) !important; }

      .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 18px;
        background: linear-gradient(90deg, #0f1b23 0%, #111f28 100%);
        border-radius: var(--radius);
        box-shadow: 0 8px 26px var(--shadow);
        margin-bottom: 18px;
      }

      .brand {
        display: flex;
        align-items: center;
        gap: 14px;
        font-weight: 700;
        font-size: 22px;
      }

      .brand-mark {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: conic-gradient(from 160deg, var(--accent), #1a6d76, #0b2a34, var(--accent));
        box-shadow: inset 0 0 18px rgba(29, 179, 184, 0.6);
      }

      .search {
        flex: 1;
        max-width: 520px;
        margin: 0 18px;
        background: #0c141a;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 999px;
        padding: 8px 18px;
        color: var(--muted);
      }

      .user {
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--text);
      }

      .user .avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(160deg, #2b8b91, #0f1b23);
        border: 1px solid rgba(255,255,255,0.1);
      }

      .card {
        background: linear-gradient(180deg, var(--panel), var(--panel2));
        border-radius: var(--radius);
        padding: 18px 18px;
        box-shadow: 0 12px 30px var(--shadow);
        border: 1px solid rgba(255,255,255,0.04);
      }

      .kpi {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .kpi .value {
        font-size: 40px;
        font-weight: 700;
      }

      .kpi .label {
        color: var(--muted);
        font-size: 14px;
        letter-spacing: 0.4px;
      }

      .kpi .delta {
        color: var(--accent);
        font-weight: 600;
        font-size: 14px;
      }

      .section-title {
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 12px;
      }

      .list-row {
        display: grid;
        grid-template-columns: 44px 1fr auto;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
      }

      .list-row:last-child { border-bottom: none; }

      .pill {
        background: rgba(29, 179, 184, 0.12);
        color: var(--accent);
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        border: 1px solid rgba(29, 179, 184, 0.2);
      }

      .alert-dot {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: rgba(213, 71, 71, 0.18);
        border: 1px solid rgba(213, 71, 71, 0.35);
        display: grid;
        place-items: center;
        color: #e46f6f;
        font-weight: 700;
      }

      .tiny { font-size: 12px; color: var(--muted); }

      .chart-container {
        background: linear-gradient(180deg, #0f1b23 0%, #101d24 100%);
        border-radius: var(--radius);
        padding: 14px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 10px 24px var(--shadow);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.markdown("## Trifecta")
st.sidebar.markdown("AI Agention Center")

status = api_get("/health", timeout=5)
if status["ok"]:
    st.sidebar.success("API Online")
    services = safe_get(status["data"], "services", {})
    if isinstance(services, dict):
        st.sidebar.markdown("**Services**")
        for service, is_up in services.items():
            st.sidebar.write(f"- {service.title()}: {'up' if is_up else 'down'}")
else:
    st.sidebar.error("API Offline")
    st.sidebar.caption(status["error"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")
for label in [
    "Dashboard",
    "Client Intake",
    "Program Delivery",
    "Progress Monitoring",
    "Marketing & Sales",
    "Finance & Invoicing",
    "Compliance",
    "Alumni Engagement",
    "AI Support",
    "Analytics",
    "Settings",
]:
    st.sidebar.write(f"- {label}")

st.sidebar.markdown("---")
st.sidebar.caption(f"API: {API_BASE_URL}")
st.sidebar.caption(f"Local time: {datetime.now().strftime('%b %d, %Y %I:%M %p')}")


# -----------------------------
# Top bar
# -----------------------------

st.markdown(
    """
    <div class="topbar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div>Trifecta</div>
      </div>
      <div class="search">Search</div>
      <div class="user">
        <div>Danielle C</div>
        <div class="avatar"></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Data
# -----------------------------

metrics = api_get("/api/dashboard/metrics")
metrics_data = metrics["data"] if metrics["ok"] else {}

kpi_total_leads = safe_get(metrics_data, "total_leads", 67)
kpi_qualified = safe_get(metrics_data, "qualified_hr_leads", 34)
kpi_revenue = safe_get(metrics_data, "revenue_mtd", 81547)
kpi_conversion = safe_get(metrics_data, "conversion_rate", 4.2)
if isinstance(kpi_conversion, str) and kpi_conversion.endswith("%"):
    kpi_conversion_display = kpi_conversion
else:
    kpi_conversion_display = f"{kpi_conversion}%"

client_activity = safe_get(metrics_data, "client_activity", [
    {"name": "Sarah Wen", "detail": "Appointment rescheduled", "when": "Today 11:00 AM"},
    {"name": "Megan Tran", "detail": "Scheduled appointment", "when": "Yesterday 3:30 PM"},
    {"name": "Emily Ross", "detail": "Completed intake form", "when": "2 days ago"},
    {"name": "Anna Patel", "detail": "Submitted intake", "when": "2 days ago"},
])

upcoming = safe_get(metrics_data, "upcoming_appointments", [
    {"date": "Apr 25, 2024", "name": "On-May", "time": "02:00 PM"},
    {"date": "Apr 26, 2024", "name": "David Kim", "time": "08:00 AM"},
])

alerts = safe_get(metrics_data, "alerts", [
    {"title": "Intake form review", "age": "2 days ago"},
    {"title": "Session notes submission pending", "age": "3 days ago"},
    {"title": "Client feedback required", "age": "1 week ago"},
])

trend_points = safe_get(metrics_data, "revenue_trend", [38, 45, 49, 63, 60, 72])


# -----------------------------
# KPI Row
# -----------------------------

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(
        f"""
        <div class="card kpi">
          <div class="value">{kpi_total_leads}</div>
          <div class="label">Total Leads</div>
          <div class="delta">+34%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col2:
    st.markdown(
        f"""
        <div class="card kpi">
          <div class="value">{kpi_qualified}</div>
          <div class="label">Qualified HR Leads</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col3:
    st.markdown(
        f"""
        <div class="card kpi">
          <div class="value">${kpi_revenue:,}</div>
          <div class="label">Monthly Revenue</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col4:
    st.markdown(
        f"""
        <div class="card kpi">
          <div class="value">{kpi_conversion_display}</div>
          <div class="label">Conversion Rate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)


# -----------------------------
# Mid Row
# -----------------------------

col_left, col_mid, col_right = st.columns([2, 1.2, 1])

with col_left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Client Activity</div>", unsafe_allow_html=True)
    for item in client_activity:
        name = safe_get(item, "name", "Unknown")
        detail = safe_get(item, "detail", "")
        when = safe_get(item, "when", "")
        st.markdown(
            f"""
            <div class="list-row">
              <div class="avatar"></div>
              <div>
                <div><strong>{name}</strong></div>
                <div class="tiny">{detail}</div>
              </div>
              <div class="tiny">{when}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_mid:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Upcoming Appointments</div>", unsafe_allow_html=True)
    for item in upcoming:
        date = safe_get(item, "date", "")
        name = safe_get(item, "name", "")
        time_label = safe_get(item, "time", "")
        st.markdown(
            f"""
            <div class="list-row">
              <div class="pill">Cal</div>
              <div>
                <div><strong>{date}</strong></div>
                <div class="tiny">{name}</div>
              </div>
              <div class="tiny">{time_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Alerts</div>", unsafe_allow_html=True)
    for item in alerts:
        title = safe_get(item, "title", "")
        age = safe_get(item, "age", "")
        st.markdown(
            f"""
            <div class="list-row">
              <div class="alert-dot">!</div>
              <div>
                <div><strong>{title}</strong></div>
                <div class="tiny">{age}</div>
              </div>
              <div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Bottom Row
# -----------------------------

col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Revenue Trend</div>", unsafe_allow_html=True)
    st.line_chart(trend_points)
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Live Checks</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='tiny'>Last refresh: {datetime.now().strftime('%I:%M %p')}</div>", unsafe_allow_html=True)
    if metrics["ok"]:
        st.markdown("<div class='pill'>Metrics: OK</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='pill'>Metrics: Placeholder</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
    if st.button("Refresh Live Data"):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Footer
# -----------------------------

st.markdown("---")
st.caption("Trifecta AI Agent Dashboard (Streamlit)")
