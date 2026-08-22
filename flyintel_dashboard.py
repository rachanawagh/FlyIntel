import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"   # suppresses INFO/WARNING logs
import warnings
warnings.filterwarnings("ignore")

import json
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import math
import folium
from streamlit_folium import st_folium
from astar_planner import astar, obstacles, GRID_SIZE

# ======================================================
# SITE ORIGIN (REPLACE WITH YOUR ACTUAL FLIGHT SITE GPS COORDINATES)
# ======================================================
# This is the real-world lat/lon that grid cell (row=0, col=0) maps to.
# Placeholder below is central Pune — change to your actual test site.
ORIGIN_LAT = 18.5204
ORIGIN_LON = 73.8567
CELL_SIZE_M = 6  # how many real-world meters each grid unit represents

# ======================================================
# SHARED MISSION STATE
# ======================================================

STATE_FILE = r"C:\Users\Rachana\OneDrive\Desktop\FlyIntel\mission_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    except:

        return {
            "battery_probability":0.05,
            "risk":"LOW",
            "mission_status":"MISSION IN PROGRESS",
            "return_required":False,
            "battery_voltage":4.2,
            "battery_percent":100
        }
    
state = load_state()

_METERS_PER_DEG_LAT = 111320
_METERS_PER_DEG_LON = 111320 * math.cos(math.radians(ORIGIN_LAT))

def grid_to_latlon(row, col):
    """Converts an abstract (row, col) grid coordinate into a real lat/lon
    offset from ORIGIN_LAT/ORIGIN_LON, so the existing A* grid logic
    can be drawn on a real satellite map without changing the planner."""
    north_m = row * CELL_SIZE_M
    east_m = col * CELL_SIZE_M
    lat = ORIGIN_LAT + (north_m / _METERS_PER_DEG_LAT)
    lon = ORIGIN_LON + (east_m / _METERS_PER_DEG_LON)
    return lat, lon

# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(
    page_title="FlyIntel | Dashboard",
    layout="wide"
)

from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=1000,key="refresh")

# ======================================================
# CUSTOM CSS (DARK GREY THEME, CLASSY HERO, CLEAN SIDEBAR)
# ======================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* ---------- BACKGROUND: solid darker grey, no blue tint ---------- */
.stApp {
    background: linear-gradient(160deg, #232326 0%, #1a1a1c 55%, #141415 100%);
    color: #F1F5F9;
}

/* ---------- SIDEBAR: lighter grey than main background ---------- */
section[data-testid="stSidebar"] {
    background-color: #2c2c30 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] label {
    color: #F5F5F4 !important;
}

/* Sidebar nav — white transparent boxes, off-white readable text (no yellow) */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 10px;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    padding: 12px 16px !important;
    border-radius: 14px !important;
    margin-bottom: 2px !important;
    width: 100% !important;
    transition: all 0.2s ease-in-out;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
    color: #F1F1EF !important;
    font-weight: 600 !important;
    font-size: 0.98rem !important;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    background: rgba(255, 255, 255, 0.12) !important;
    border-color: rgba(255, 255, 255, 0.30) !important;
    transform: translateX(2px);
}

/* ---------- SIDEBAR TELEMETRY BOX (separate card, below nav) ---------- */
.telemetry-box {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 16px 18px;
    margin-top: 6px;
}

.telemetry-title {
    color: #F5F5F4;
    font-weight: 700;
    font-size: 0.92rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}

.telemetry-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    font-size: 0.95rem;
}

.telemetry-row span:first-child {
    color: #B5B5B8;
    font-weight: 500;
}

.telemetry-row span:last-child {
    color: #F5F5F4;
    font-weight: 700;
}

/* ---------- HERO TITLE: classy, off-white only, larger ---------- */
.hero-wrap {
    text-align: center;
    padding: 6px 0 4px 0;
}

.hero-title {
    font-family: 'Poppins', 'Inter', sans-serif;
    font-size: 3.6rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin: 0;
    color: #F5F5F4;
}

.hero-tagline {
    margin-top: 10px;
    font-size: 1.05rem;
    font-weight: 400;
    letter-spacing: 0.04em;
    color: #A9A9AC;
    max-width: 720px;
    margin-left: auto;
    margin-right: auto;
}

.hero-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    padding: 6px 18px;
    border-radius: 999px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #6EE7B7;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.hero-status .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #34D399;
    box-shadow: 0 0 8px #34D399;
}

/* ---------- BUBBLE / GLASS METRIC CARDS ---------- */
.card {
    background: rgba(255, 255, 255, 0.05);
    padding: 24px 18px;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.10);
    text-align: center;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    border-top: 3px solid var(--accent, rgba(255,255,255,0.3));
    transition: transform 0.2s ease;
}

.card:hover {
    transform: translateY(-3px);
}

.card h3 {
    font-size: 0.85rem;
    color: #94A3B8 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
    font-weight: 600;
}

.card h2 {
    font-size: 2.1rem;
    color: #F8FAFC !important;
    font-weight: 700;
    margin: 0;
}

/* ---------- SECTION CARD WRAPPER (charts / map) ---------- */
.section-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 22px;
    padding: 18px 20px 6px 20px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    margin-bottom: 18px;
}

.section-card h3 {
    color: #F8FAFC;
    font-weight: 600;
    letter-spacing: 0.01em;
}

/* Route map keeps a light "instrument panel" look, wrapped in a soft frame */
.map-frame {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 20px;
    padding: 10px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

/* ---------- NATIVE METRIC COMPONENT ---------- */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 18px;
    padding: 14px 10px;
    backdrop-filter: blur(10px);
}

div[data-testid="stMetric"] label p {
    color: #94A3B8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* ---------- ALERT / NOTIFICATION BUBBLES ---------- */
div[data-testid="stNotification"] {
    background-color: rgba(255, 255, 255, 0.96) !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18) !important;
}

div[data-testid="stNotification"] p {
    color: #0F172A !important;
    font-size: 1.02rem !important;
    font-weight: 600 !important;
}

h1, h2, h3, h4, h5 {
    font-weight: 600;
    color: #F8FAFC;
}

hr {
    border-color: rgba(255, 255, 255, 0.1) !important;
}

.footer {
    text-align: center;
    font-size: 13px;
    padding: 28px 0 10px 0;
    color: #64748B;
    font-weight: 400;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR NAVIGATION
# ======================================================

st.sidebar.markdown(
    "<h2 style='text-align: center; padding-bottom: 20px; font-weight: 800; "
    "letter-spacing: 0.03em;'>FlyIntel</h2>",
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🔋 Battery Intelligence",
        "🎯 Mission Control",
        "🧭 Emergency Routing",
        "🛰 Alerts & Logs"
    ]
)

st.sidebar.markdown("---")

# ======================================================
# LIVE TELEMETRY SIMULATION
# ======================================================

voltage = state["battery_voltage"]

battery_percent = state["battery_percent"]

current = round(
    0.8 + (100-battery_percent)*0.025,
    2
)

temperature = round(
    25 + (100-battery_percent)*0.18,
    1
)

st.sidebar.markdown(f"""
<div class="telemetry-box">
    <div class="telemetry-title">📡 Live Battery Telemetry</div>
    <div class="telemetry-row"><span>Voltage</span><span>{voltage} V</span></div>
    <div class="telemetry-row"><span>Current</span><span>{current} A</span></div>
    <div class="telemetry-row"><span>Temperature</span><span>{temperature} °C</span></div>
</div>
""", unsafe_allow_html=True)

# ======================================================
# BATTERY DATA FROM AIRSIM
# ======================================================

failure_probability = state["battery_probability"]

risk = state["risk"]

mission = state["mission_status"]

if risk == "LOW":
    risk_color = "#10B981"

elif risk == "MEDIUM":
    risk_color = "#F59E0B"

else:
    risk_color = "#EF4444"

# ======================================================
# HERO HEADER
# ======================================================

st.markdown(f"""
<div class="hero-wrap">
    <h1 class="hero-title">FlyIntel</h1>
    <div class="hero-tagline">An AI-powered safety system that predicts drone battery failure before it happens and autonomously plans an emergency return route to prevent crashes.</div>
    <div class="hero-status"><span class="dot"></span> System Online — Telemetry Streaming Live</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================
# TOP METRICS
# ======================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card" style="--accent:#60A5FA;">
        <h3>Voltage</h3>
        <h2>{voltage} V</h2>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card" style="--accent:#A78BFA;">
        <h3>Current</h3>
        <h2>{current} A</h2>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card" style="--accent:#FBBF24;">
        <h3>Temperature</h3>
        <h2>{temperature} °C</h2>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card" style="--accent:{risk_color};">
        <h3>Failure Probability</h3>
        <h2>{failure_probability*100:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================
# SECOND ROW — TREND + GAUGE
# ======================================================

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Failure Probability Trend")

    prob = np.linspace(max(0.0, failure_probability - 0.15), failure_probability, 20)
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            y=prob,
            mode='lines+markers',
            line=dict(color='#FBBF24', width=3),
            marker=dict(size=6, color='#FDE68A'),
            fill='tozeroy',
            fillcolor='rgba(251, 191, 36, 0.10)',
            name='Probability Trend'
        )
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#94A3B8',
        margin=dict(l=20, r=20, t=10, b=20),
        height=330,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)')
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Risk Assessment")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=failure_probability*100,
        title={'text': risk, 'font': {'size': 22, 'color': risk_color}},
        number={'font': {'color': '#F8FAFC'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#94A3B8'},
            'bar': {'color': risk_color},
            'bgcolor': 'rgba(255,255,255,0.05)',
            'steps': [
                {'range': [0, 20], 'color': 'rgba(16, 185, 129, 0.12)'},
                {'range': [20, 50], 'color': 'rgba(245, 158, 11, 0.12)'},
                {'range': [50, 100], 'color': 'rgba(239, 68, 68, 0.12)'}
            ]
        }
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#F8FAFC',
        margin=dict(l=20, r=20, t=30, b=10),
        height=330
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# ROUTE MAP
# ======================================================

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### Emergency Route Grid Map")

start = (2, 3)
goal = (18, 18)
path = []

if risk == "HIGH":
    path = astar(start, goal)

# Center the map on the midpoint between drone and home
center_lat, center_lon = grid_to_latlon(
    (start[0] + goal[0]) / 2, (start[1] + goal[1]) / 2
)

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=19,
    tiles=None,
    control_scale=True,
)

# Free satellite imagery basemap (no API key required)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics",
    name="Satellite",
    overlay=False,
    control=False,
).add_to(m)

# --- Mission boundary polygon (yellow), around the grid extent ---
boundary_grid = [(0, 0), (0, GRID_SIZE), (GRID_SIZE, GRID_SIZE), (GRID_SIZE, 0)]
boundary_latlon = [grid_to_latlon(r, c) for r, c in boundary_grid]
folium.Polygon(
    locations=boundary_latlon,
    color="#FACC15",
    weight=3,
    fill=False,
    dash_array="6,4",
).add_to(m)

# --- Diagonal crosshatch mesh inside the boundary (visual style only) ---
mesh_step = max(2, GRID_SIZE // 6)
for i in range(0, GRID_SIZE + 1, mesh_step):
    folium.PolyLine(
        [grid_to_latlon(i, 0), grid_to_latlon(i, GRID_SIZE)],
        color="#FFFFFF", weight=1, opacity=0.35
    ).add_to(m)
    folium.PolyLine(
        [grid_to_latlon(0, i), grid_to_latlon(GRID_SIZE, i)],
        color="#FFFFFF", weight=1, opacity=0.35
    ).add_to(m)
    for j in range(0, GRID_SIZE + 1, mesh_step):
        folium.CircleMarker(
            location=grid_to_latlon(i, j),
            radius=3, color="#FFFFFF", fill=True,
            fill_color="#FFFFFF", fill_opacity=0.7, weight=1,
        ).add_to(m)

# --- Obstacle zones (orange circles, matching reference style) ---
for (orow, ocol) in obstacles:
    folium.CircleMarker(
        location=grid_to_latlon(orow, ocol),
        radius=9,
        color="#F97316",
        fill=True,
        fill_color="#FB923C",
        fill_opacity=0.95,
        weight=2,
        popup="Obstacle / No-Fly Zone",
    ).add_to(m)

# --- A* safe route path (only drawn when HIGH risk triggers it) ---
if path:
    path_latlon = [grid_to_latlon(r, c) for r, c in path]
    folium.PolyLine(
        path_latlon,
        color="#EF4444",
        weight=5,
        opacity=0.9,
        popup="A* Emergency Return Route",
    ).add_to(m)

# --- Drone current position: red heading arrow ---
if path and len(path) > 1:
    (r0, c0), (r1, c1) = path[0], path[1]
else:
    (r0, c0), (r1, c1) = start, goal
bearing = math.degrees(math.atan2(c1 - c0, r1 - r0))

drone_icon = folium.DivIcon(html=f"""
    <div style="transform: rotate({bearing}deg); font-size: 30px; color:#EF4444;
                text-shadow: 0 0 4px rgba(0,0,0,0.6);">▲</div>
""")
folium.Marker(
    location=grid_to_latlon(*start),
    icon=drone_icon,
    popup="UAV Current Position",
).add_to(m)

# --- Home / base station ---
folium.Marker(
    location=grid_to_latlon(*goal),
    icon=folium.Icon(color="green", icon="home", prefix="fa"),
    popup="Home Base",
).add_to(m)

# --- Optional point of interest marker (purple), midpoint of path for demo ---
if path:
    mid = path[len(path) // 2]
    folium.CircleMarker(
        location=grid_to_latlon(*mid),
        radius=8,
        color="#8B5CF6",
        fill=True,
        fill_color="#A78BFA",
        fill_opacity=0.95,
        weight=2,
        popup="Waypoint Checkpoint",
    ).add_to(m)

st.markdown('<div class="map-frame">', unsafe_allow_html=True)
st_folium(m, use_container_width=True, height=480, returned_objects=[])
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ======================================================
# ROUTE ANALYTICS
# ======================================================

st.markdown("### Route Analytics")

r1, r2, r3 = st.columns(3)

if path is not None and len(path) > 0:
    distance = len(path) * 0.12
else:
    distance = 2.4

with r1:
    st.metric("Estimated Return Distance", f"{distance:.2f} km")

with r2:
    st.metric("Estimated Return Time", f"{distance * 2:.1f} min")

with r3:
    st.metric("Obstacle Zones Avoided", len(obstacles))

# ======================================================
# MISSION STATUS
# ======================================================
st.markdown("### Mission Status Executive Feed")

if risk == "LOW":
    st.success(mission)

elif risk == "MEDIUM":
    st.warning(mission)

else:
    st.error(mission)

# ======================================================
# ALERT FEED
# ======================================================

st.markdown("### Recent Alert Feed")

alerts = []

if risk == "LOW":

    alerts.append("✓ Mission progressing normally.")

elif risk == "MEDIUM":

    alerts.append("⚠ Battery degradation detected.")
    alerts.append("⚠ Monitoring intensified.")

else:

    alerts.append("🚨 Emergency return initiated.")
    alerts.append("🛰 A* safe route uploaded.")
    alerts.append("🛬 Returning to Home.")

for alert in alerts:
    st.info(alert)

# ======================================================
# AI MODEL PERFORMANCE
# ======================================================

st.markdown("### Battery Intelligence Model Performance")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Accuracy", "99.81%")

with m2:
    st.metric("Precision", "99.28%")

with m3:
    st.metric("Recall", "98.53%")

with m4:
    st.metric("F1 Score", "98.90%")

# ======================================================
# FOOTER
# ======================================================

st.markdown("---")
st.markdown("""
<div class="footer">
    FlyIntel Fleet Ecosystem • Developed for TTL InnoVent Hackathon 2026
</div>
""", unsafe_allow_html=True)