import streamlit as st
import os
import urllib.request
from datetime import datetime, timedelta
import pandas as pd
from skyfield.api import load, EarthSatellite, utc
from scipy.spatial.distance import euclidean
import numpy as np
import plotly.graph_objects as go

# ---- Parameters ----
COLLISION_THRESHOLD_KM = 5.0
PROPAGATION_STEPS = 144  # 24h, every 10 minutes
MAX_SATELLITES = 20

# ---- Step 1: Download & Load TLEs ----
@st.cache_resource(show_spinner=False)
def download_and_load_satellites(tle_path='active_tles.txt'):
    if not os.path.exists(tle_path):
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
        urllib.request.urlretrieve(url, tle_path)

    with open(tle_path, 'r') as file:
        lines = file.readlines()

    satellites = []
    for i in range(0, len(lines), 3):
        name = lines[i].strip()
        try:
            sat = EarthSatellite(lines[i+1].strip(), lines[i+2].strip(), name)
            satellites.append((name, sat))
        except:
            continue
        if len(satellites) >= MAX_SATELLITES:
            break
    return satellites

# ---- Step 2: Propagate Orbits ----
@st.cache_resource(show_spinner=False)
def propagate_satellites(_satellites):
    ts = load.timescale()
    now = datetime.now(utc)
    times = [ts.utc(now + timedelta(minutes=10 * i)) for i in range(PROPAGATION_STEPS)]

    data = []
    for name, sat in _satellites:
        for t in times:
            pos = sat.at(t).position.km
            data.append({
                'satellite': name,
                'time': t.utc_strftime('%Y-%m-%d %H:%M:%S'),
                'x_km': pos[0],
                'y_km': pos[1],
                'z_km': pos[2]
            })
    return pd.DataFrame(data)

# ---- Step 3: Create NEW Satellite Path ----
def create_new_satellite(name, radius, z_amplitude):
    now = datetime.now(utc)
    times = [now + timedelta(minutes=10 * i) for i in range(PROPAGATION_STEPS)]

    data = []
    for i, t in enumerate(times):
        theta = 2 * np.pi * i / PROPAGATION_STEPS
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        z = z_amplitude * np.sin(2 * theta)
        data.append({
            'satellite': name,
            'time': t.strftime('%Y-%m-%d %H:%M:%S'),
            'x_km': x,
            'y_km': y,
            'z_km': z
        })
    return pd.DataFrame(data)

# ---- Step 4: Detect Possible Collisions ----
def detect_collisions(df, target_sat):
    grouped = df.groupby('time')
    collisions = []

    for time, group in grouped:
        new_sat = group[group['satellite'] == target_sat]
        if new_sat.empty:
            continue

        pos1 = (new_sat.iloc[0]['x_km'], new_sat.iloc[0]['y_km'], new_sat.iloc[0]['z_km'])
        for _, row in group.iterrows():
            if row['satellite'] == target_sat:
                continue
            pos2 = (row['x_km'], row['y_km'], row['z_km'])
            distance = euclidean(pos1, pos2)
            if distance < COLLISION_THRESHOLD_KM:
                collisions.append({
                    'time': time,
                    'sat1': target_sat,
                    'sat2': row['satellite'],
                    'distance_km': distance
                })

    return pd.DataFrame(collisions)

# ---- Step 5: Interactive Plot with Plotly ----
def plot_with_plotly(df, collision_df):
    fig = go.Figure()
    unique_sats = df['satellite'].unique()

    for sat in unique_sats:
        sat_df = df[df['satellite'] == sat]
        fig.add_trace(go.Scatter3d(
            x=sat_df['x_km'],
            y=sat_df['y_km'],
            z=sat_df['z_km'],
            mode='lines',
            name=sat,
            hoverinfo='text',
            text=[f"Satellite: {sat}<br>Time: {t}<br>X: {x:.1f} Y: {y:.1f} Z: {z:.1f}" for t, x, y, z in zip(sat_df['time'], sat_df['x_km'], sat_df['y_km'], sat_df['z_km'])],
            line=dict(width=2)
        ))

    if not collision_df.empty:
        merged = pd.merge(collision_df, df, left_on=['time', 'sat2'], right_on=['time', 'satellite'])
        fig.add_trace(go.Scatter3d(
            x=merged['x_km'],
            y=merged['y_km'],
            z=merged['z_km'],
            mode='markers',
            name='Collision Risk',
            marker=dict(color='red', size=5, symbol='diamond'),
            text=[f"🚨 Collision at {t}<br>With: {s}" for t, s in zip(merged['time'], merged['satellite'])],
            hoverinfo='text'
        ))

    fig.update_layout(
        title="🛰️ Satellite Orbits and Collision Prediction",
        scene=dict(
            xaxis_title="X (km)",
            yaxis_title="Y (km)",
            zaxis_title="Z (km)",
            bgcolor="black",
            xaxis=dict(color='white'),
            yaxis=dict(color='white'),
            zaxis=dict(color='white')
        ),
        legend=dict(font=dict(color='white')),
        font=dict(color='white'),
        paper_bgcolor='black',
        width=1200,
        height=800
    )

    return fig

# ---- Streamlit App ----
st.set_page_config(layout="wide")
st.title("🚀 Satellite Collision Prediction")

with st.sidebar:
    st.header("Custom Satellite Input")
    new_sat_name = st.text_input("New Satellite Name", value="NEW_SAT")
    radius = st.number_input("Orbital Radius (km)", min_value=6000, max_value=8000, value=7050)
    z_amp = st.number_input("Z-axis Amplitude (km)", min_value=0, max_value=1000, value=500)

with st.spinner("Loading satellite data and propagating orbits..."):
    all_sats = download_and_load_satellites()
    df_existing = propagate_satellites(all_sats)
    df_new = create_new_satellite(new_sat_name, radius, z_amp)

    full_df = pd.concat([df_existing, df_new])
    collision_df = detect_collisions(full_df, new_sat_name)

if not collision_df.empty:
    st.error(f"🚨 WARNING: Possible collisions detected with {new_sat_name}:")
    st.dataframe(collision_df)
else:
    st.success(f"✅ {new_sat_name} trajectory is safe.")
satellites = sorted(full_df['satellite'].unique())
#st.write(satellites)

fig = plot_with_plotly(full_df, collision_df)
st.plotly_chart(fig, use_container_width=True)


