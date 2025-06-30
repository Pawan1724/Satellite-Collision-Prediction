import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from skyfield.api import load, EarthSatellite
from scipy.spatial.distance import euclidean
import urllib.request
import os

# ---- Parameters ----
COLLISION_THRESHOLD_KM = 5.0
PROPAGATION_STEPS = 144  # every 10 min for 24h
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

# ---- Load Satellite TLEs ----
@st.cache_resource
def download_and_load_satellites(tle_path='active_tles.txt', max_sats=20):
    try:
        if not os.path.exists(tle_path):
            urllib.request.urlretrieve(TLE_URL, tle_path)
           
        with open(tle_path, 'r') as f:
            lines = f.readlines()

        satellites = []
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
            name = lines[i].strip()
            try:
                sat = EarthSatellite(lines[i + 1], lines[i + 2], name)
                satellites.append((name, sat))
            except Exception as e:
                st.warning(f"Failed to parse TLE for {name}: {e}")
                continue
            if len(satellites) >= max_sats:
                break
        
        return satellites
    except Exception as e:
        st.error(f"Error loading TLEs: {e}")
        return []

# ---- Propagate Satellite Positions ----
def propagate_satellites(satellites, ts):
    try:
        now = datetime.now(timezone.utc)
        times = [ts.utc(now + timedelta(minutes=10 * i)) for i in range(PROPAGATION_STEPS)]
        records = []

        for name, sat in satellites:
            for t in times:
                try:
                    pos = sat.at(t).position.km
                    records.append({
                        "satellite": name,
                        "time": t.utc_strftime('%Y-%m-%d %H:%M:%S'),
                        "x_km": pos[0],
                        "y_km": pos[1],
                        "z_km": pos[2]
                    })
                except Exception as e:
                    st.warning(f"Error propagating {name} at {t.utc_strftime('%Y-%m-%d %H:%M:%S')}: {e}")
                    continue
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        st.error(f"Error in propagation: {e}")
        return pd.DataFrame()

# ---- Create Custom Satellite with Cartesian Coordinates ----
def create_custom_satellite(name, x_km, y_km, z_km, ts):
    try:
        now = datetime.now(timezone.utc)
        times = [ts.utc(now + timedelta(minutes=10 * i)) for i in range(PROPAGATION_STEPS)]
        records = []

        for t in times:
            records.append({
                "satellite": name,
                "time": t.utc_strftime('%Y-%m-%d %H:%M:%S'),
                "x_km": x_km,
                "y_km": y_km,
                "z_km": z_km
            })
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        st.error(f"Error creating custom satellite: {e}")
        return pd.DataFrame()

# ---- Collision Detection ----
def detect_collisions(df, new_sat_name):
    try:
        collisions = []
        grouped = df.groupby("time")

        for time, group in grouped:
            new_sat = group[group["satellite"] == new_sat_name]
            others = group[group["satellite"] != new_sat_name]
            if new_sat.empty:
                continue
            pos1 = new_sat.iloc[0][["x_km", "y_km", "z_km"]].values
            for _, row in others.iterrows():
                pos2 = row[["x_km", "y_km", "z_km"]].values
                dist = euclidean(pos1, pos2)
                if dist < COLLISION_THRESHOLD_KM:
                    collisions.append({
                        "time": time,
                        "sat1": new_sat_name,
                        "sat2": row["satellite"],
                        "distance_km": dist
                    })

        collision_df = pd.DataFrame(collisions)
        return collision_df
    except Exception as e:
        st.error(f"Error detecting collisions: {e}")
        return pd.DataFrame()

# ---- 3D Visualization ----
def plot_3d(df, collision_df):
    try:
        fig = go.Figure()
        if df.empty:
            return fig

        sats = df["satellite"].unique()

        for sat in sats:
            sat_df = df[df["satellite"] == sat]
            fig.add_trace(go.Scatter3d(
                x=sat_df["x_km"], y=sat_df["y_km"], z=sat_df["z_km"],
                mode="lines",
                name=sat,
                hovertext=[f"{sat} | {t}" for t in sat_df["time"]],
                hoverinfo="text",
                line=dict(width=2)
            ))

        if not collision_df.empty:
            merged = pd.merge(collision_df, df, left_on=["time", "sat2"], right_on=["time", "satellite"])
            fig.add_trace(go.Scatter3d(
                x=merged["x_km"], y=merged["y_km"], z=merged["z_km"],
                mode="markers",
                marker=dict(color="red", size=5, symbol="x"),
                name="Collision Risk",
                hovertext=[f"🚨 {r['sat2']} @ {r['time']} ({r['distance_km']:.2f} km)" for _, r in collision_df.iterrows()],
                hoverinfo="text"
            ))

        fig.update_layout(
            title="🛰️ Satellite Trajectories & Collision Prediction",
            scene=dict(
                xaxis_title="X (km)", yaxis_title="Y (km)", zaxis_title="Z (km)",
                bgcolor="black",
                xaxis=dict(color="white"), yaxis=dict(color="white"), zaxis=dict(color="white")
            ),
            legend=dict(font=dict(color="white")),
            paper_bgcolor="black",
            font=dict(color="white"),
            width=1200,
            height=800
        )
        return fig
    except Exception as e:
        st.error(f"Error creating plot: {e}")
        return go.Figure()

# ---- Fallback: Generate Collision-Prone Coordinates ----
def get_collision_prone_coords(df_existing):
    if not df_existing.empty:
        first_sat = df_existing[df_existing["satellite"] == df_existing["satellite"].iloc[0]]
        first_pos = first_sat.iloc[0]
        return {
            "x_km": first_pos["x_km"] + 2.0,  # Offset by 2 km to ensure collision
            "y_km": first_pos["y_km"] + 2.0,
            "z_km": first_pos["z_km"] + 2.0
        }
    return {"x_km": 1338.5367313501306, "y_km": 2755.3187548439237, "z_km": -6677.154458033904}



st.set_page_config(layout="wide", page_title="Satellite Collision Predictor")
st.title("🛰️ Satellite Collision Predictor")


with st.sidebar:
    st.header("📡 New Satellite Input")
    new_sat_name = st.text_input("Satellite Name", "NEW_SAT")
    default_coords = {"x_km": 1338.5367313501306, "y_km": 2755.3187548439237, "z_km": -6677.154458033904}
    use_collision_coords = st.checkbox("Use collision-prone coordinates (for testing)")
    
    if use_collision_coords:
        ts = load.timescale()
        existing_sats = download_and_load_satellites()
        if existing_sats:
            df_existing = propagate_satellites(existing_sats, ts)
            default_coords = get_collision_prone_coords(df_existing)
            
    x_km = st.number_input("X Coordinate (km)", value=default_coords["x_km"], format="%.6f")
    y_km = st.number_input("Y Coordinate (km)", value=default_coords["y_km"], format="%.6f")
    z_km = st.number_input("Z Coordinate (km)", value=default_coords["z_km"], format="%.6f")
    predict_btn = st.button("🔍 Predict Collision")

if predict_btn:
    with st.spinner("Processing..."):
        try:
            ts = load.timescale()
            existing_sats = download_and_load_satellites()
            if not existing_sats:
                st.error("No satellites loaded. Check TLE data source or internet connection.")
            else:
                df_existing = propagate_satellites(existing_sats, ts)
                if df_existing.empty:
                    st.error("Failed to propagate existing satellites.")
                else:
                    df_new = create_custom_satellite(new_sat_name, x_km, y_km, z_km, ts)
                    if df_new.empty:
                        st.error("Failed to create custom satellite data.")
                    else:
                        full_df = pd.concat([df_existing, df_new])
                        collisions = detect_collisions(full_df, new_sat_name)
                        if not collisions.empty:
                            st.error("🚨 Collision risk detected!")
                            st.dataframe(collisions)
                        else:
                            st.success("✅ No collision risk detected.")
                            st.write("Try using collision-prone coordinates or adjusting the position closer to an existing satellite.")

                        st.plotly_chart(plot_3d(full_df, collisions), use_container_width=True)

                       
        except Exception as e:
            st.error(f"Critical error: {e}")
            st.write("Please check your inputs and ensure all dependencies are installed.")
