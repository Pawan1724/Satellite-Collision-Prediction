# 🛰️ Satellite Collision Prediction with Streamlit

An interactive web application that simulates and visualizes potential satellite collisions using real-world orbital data. This tool enables users to input parameters for a newly launched satellite and checks if it might come dangerously close to existing satellites.

---

## 📦 Features

- ✅ Real-time TLE data fetching from [CelesTrak](https://celestrak.org/)
- 🛰️ Simulates 3D satellite trajectories using `Skyfield`
- 📊 Visualizes orbits in interactive Plotly 3D graph
- ⚠️ Detects potential close approaches (< 5 km)
- 🧠 Accepts user-defined satellite parameters from Streamlit sidebar
- 🖱️ Hover on orbit lines to see satellite name and coordinates
- 📘 Shows index of all tracked satellites

---

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/satellite-collision-streamlit.git
cd satellite-collision-streamlit

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run Detection.py
```

---

## 🖥️ How to Use

1. Launch the app using `streamlit run Detection.py`
2. In the **sidebar**, enter:
   - Satellite Name (e.g., `NEW_SAT`)
   - Orbit Radius (e.g., `7050`)
   - Z-Amplitude (e.g., `500`)
3. Wait for the simulation to load.
4. View:
   - All orbit paths with different colors
   - Hover on paths to see satellite name and coordinates
   - Collision alerts and tracked satellite index

---

## 📂 File Structure

```
├── Detection.py            # Streamlit app (main file)
├── active_tles.txt         # Downloaded TLE data (auto-generated)
├── requirements.txt        # Python package requirements
└── README.md               # Project documentation
```

---

## 🧠 Accuracy Overview

| Factor                       | Accuracy     | Notes                                                                 |
|-----------------------------|--------------|-----------------------------------------------------------------------|
| Orbit Propagation (SGP4)    | ⭐⭐⭐⭐☆       | Accurate within ~1-5 km for short-term predictions                   |
| TLE Data                    | ⭐⭐⭐⭐☆       | Accurate if TLE is updated (valid ~3 days)                           |
| Collision Logic (3D Check)  | ⭐⭐⭐☆☆       | Based on simple Euclidean proximity, does not account for vectors    |
| Realism of Custom Orbit     | ⭐⭐☆☆☆       | Synthetically generated; user-defined radius and path                 |

> **Note**: This tool is best used for educational, research, or visualization purposes. It is not intended for official satellite mission safety validation.

---

## 📈 Example Use Cases

- Educational demos on satellite motion and collision detection
- Visualizing the risk of adding new objects to crowded orbits
- Orbit modeling practice with TLE data
- Teaching SGP4 and orbit propagation concepts

---

## 🧾 Requirements

```
streamlit skyfield plotly  pandas numpy scipy tqdm
```

> You can install them all using `pip install -r requirements.txt`

---

## 👤 Author

**Salikanti Pawan Kumar**  
AI/ML & Space Enthusiast  
GitHub: [github.com/Pawan1724](https://github.com/Pawan1724)

---

## 📃 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to use, modify, and distribute.

---
