# 🛰️ Space Debris Tracker

[![Databricks](https://img.shields.io/badge/Databricks-Apps-FF3621?style=for-the-badge&logo=databricks&logoColor=white)](https://space-debris-tracker-7474652642146548.aws.databricksapps.com)
[![Three.js](https://img.shields.io/badge/Three.js-r128-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> A real-time 3D visualization platform for tracking 8,000+ orbital debris objects, operational satellites, and collision risk assessment — built on Databricks Apps with Three.js, Flask, and Skyfield.

---

## 📸 Screenshots

> *Add screenshots to the `screenshots/` folder and they will appear here. Recommended captures:*

| View | Description |
| --- | --- |
| ![Globe View](screenshots/globe-view.png) | Interactive 3D Earth with live satellite markers |
| ![Dashboard](screenshots/dashboard.png) | Analytics dashboard with charts and risk metrics |
| ![Debris Catalog](screenshots/debris-catalog.png) | Sortable catalog of tracked objects |
| ![Celestial Bodies](screenshots/celestial-bodies.png) | Moon, Mars, and Sun orbital data |
| ![Mobile View](screenshots/mobile-view.png) | Responsive mobile interface |

---

## ✨ Features

### Interactive 3D Globe
* **Real-time satellite tracking** — 8,000+ objects rendered as 3D markers on an Earth globe
* **Orbital shell filters** — Isolate LEO, MEO, GEO, or HEO altitude regimes
* **Object type filters** — Payloads, Rocket Bodies, Debris, Unknown objects
* **Country filters** — Filter by operator nation (USA, Russia, China, etc.)
* **Preset filters** — Starlink, OneWeb, GNSS, Weather, Earth Observation constellations
* **Density control** — Adjustable level-of-detail slider (5K–35K objects)
* **Visual layers** — Day/night terminator, orbital shells, approach vectors, density heatmap

### Celestial Body Navigation
* **Switch between** Earth, Moon, Mars, and Sun views
* **Per-body filtering** — Each body maintains its own marker set and filters
* **Solar system overview** — Universe mode showing all bodies in context

### Analytics Dashboard
* **Orbital density profile** — Objects vs altitude area chart
* **Shell distribution** — LEO/MEO/GEO/HEO object counts and collision risk
* **Collision risk scoring** — ML-based probability assessment per object
* **Top 15 risk objects** — Ranked by orbital density and conjunction probability
* **Re-entry risk heatmap** — 2D density matrix of decay probability vs time-to-impact

### Debris Catalog
* **Sortable table** — Name, type, altitude, inclination, owner, decay status
* **Search & filter** — By name, country, object type, altitude shell
* **Export** — CSV, JSON, and TLE format downloads
* **Detailed view** — Per-object ephemeris, raw TLE, Python snippet, track-on-globe

### Conjunction Assessment
* **Collision prediction** — Time of Closest Approach (TCA), miss distance, combined risk score
* **Conjunction summary** — Aggregated risk distribution across altitude bands
* **CDM export** — Conjunction Data Message format

### Academy Section
* **Educational content** — Orbital mechanics, debris mitigation regulations, audience-specific explanations
* **Interactive glossary** — Expandable sections with citizen and expert definitions
* **Code examples** — Python snippets using Skyfield for SGP4 propagation

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| **Hosting** | Databricks Apps | Serverless app deployment & compute |
| **Backend** | Flask + Gunicorn | HTTP server, TLE fetch, Skyfield propagation |
| **3D Engine** | Three.js (r128) | WebGL globe, satellite markers, orbit visualization |
| **Orbital Physics** | Skyfield / SGP4-SDP4 | Satellite position computation from TLE data |
| **Charts** | Chart.js | Dashboard analytics, density profiles, risk distributions |
| **Web Worker** | orbital-worker.js | Background orbit computation to prevent UI blocking |
| **Data Source** | Celestrak (NORAD) | Two-Line Element (TLE) satellite catalog |
| **Catalog Data** | SATCAT | Satellite catalog with ownership, type, and status |
| **Space Weather** | NOAA SWPC | Solar flux, geomagnetic indices for re-entry forecasting |

---

## 🏗️ Architecture

```
Celestrak TLE API
        │
        ▼
  Flask Server (app.py)
  ├── Skyfield SGP4 Propagation → Real-time positions
  ├── SATCAT Catalog → Object metadata
  ├── Collision Risk Model → ML predictions
  └── JSON API → Embedded data modules
        │
        ▼
  Three.js Frontend (index.html)
  ├── 3D Globe + Textures (Earth, Moon, Mars, Sun)
  ├── Web Worker (orbital-worker.js) → Background computation
  ├── Chart.js Dashboard → Analytics & risk visualization
  └── Interactive Filters → LEO/MEO/GEO/HEO, type, country
```

---

## 📁 Project Structure

```
Space-Debris-Project/
├── .gitignore                    # Prevents backup/data clutter
├── README.md                     # This file
├── LICENSE                       # MIT License
├── CNAME                         # Custom domain (space-debris.com)
│
├── webapp/                       # Production Databricks App
│   ├── index.html               # Main 3D visualization (single-page app, ~447 KB)
│   ├── app.py                   # Flask server — TLE fetch, Skyfield propagation, API routes
│   ├── app.yaml                 # Databricks App deployment config
│   ├── requirements.txt         # Python dependencies
│   ├── three.min.js             # Three.js r128 library
│   ├── orbital-worker.js       # Web Worker for orbit calculations
│   ├── embedded_*.js            # Embedded data modules (stats, predictions, collision, celestial)
│   ├── *.json                   # Data files (satcat, collision risk, celestial, positions)
│   └── *-texture.jpg            # Planet textures (Earth, Mars, Moon, Sun)
│
├── data/                         # Datasets
│   ├── raw/                      # Original CSV and TLE data
│   │   ├── space_debris_raw.csv
│   │   └── space_debris_cleaned.csv
│   └── processed/               # Cleaned JSON for the app
│       ├── satellite_positions.json
│       ├── satcat_catalog.json
│       ├── satcat_stats.json
│       └── ml_predictions.json
│
├── Jupyter Notebooks/            # ML & analysis notebooks
│   ├── Space Debris Tracking Platform    # Main data pipeline
│   ├── Space Debris ML Modeling          # Collision risk ML model
│   └── space-debris-project              # Exploratory analysis
│
├── docs/                         # GitHub Pages deployment
│   ├── index.html               # Hosted demo version
│   ├── CNAME                    # Custom domain config
│   └── (supporting assets)
│
└── screenshots/                  # README images (add your own)
```

---

## 🌐 Live Demo

| Environment | URL |
| --- | --- |
| **Databricks App (production)** | [space-debris-tracker-7474652642146548.aws.databricksapps.com](https://space-debris-tracker-7474652642146548.aws.databricksapps.com) |
| **GitHub Pages** | [space-debris.com](https://space-debris.com) |

---

## 🚀 Installation

### Prerequisites
* Python 3.9+
* pip

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Guruvendra47/Space-Debris-Project.git
cd Space-Debris-Project/webapp

# Install dependencies
pip install -r requirements.txt

# Run the Flask server
python app.py

# Open in browser
# http://localhost:8000
```

---

## ☁️ Databricks Deployment

This app is deployed as a **Databricks App** (Apps V2):

```bash
# Deploy from the webapp directory
databricks apps deploy space-debris-tracker \
  --source-code-path /Workspace/.../Space-Debris-Project/webapp
```

The `app.yaml` configures:
* **Entrypoint:** `python app.py`
* **Dependencies:** flask, flask-compress, gunicorn, skyfield, numpy
* **Compute:** Medium serverless

---

## 📊 Data Sources

| Source | Description | URL |
| --- | --- | --- |
| **Celestrak** | NORAD Two-Line Element sets for satellite orbits | [celestrak.org](https://celestrak.org/) |
| **SATCAT** | Satellite catalog — ownership, type, launch date, status | [celestrak.org/satcat](https://celestrak.org/satcat/) |
| **NOAA SWPC** | Space weather — solar flux, geomagnetic indices | [swpc.noaa.gov](https://swpc.noaa.gov/) |

TLE data is fetched at app startup and propagated using Skyfield's SGP4/SDP4 implementation for accurate real-time positions.

---

## 🌍 Orbital Shell Definitions

| Shell | Altitude Range | Description |
| --- | --- | --- |
| **LEO** | 0 – 2,000 km | Low Earth Orbit — ISS, Starlink, most debris |
| **MEO** | 2,000 – 35,000 km | Medium Earth Orbit — GNSS (GPS, Galileo) |
| **GEO** | 35,000 – 37,000 km | Geostationary Orbit — Communications, weather |
| **HEO** | > 37,000 km | High Earth Orbit — Highly elliptical, deep space |

---

## 🤖 ML Collision Risk Model

The collision risk model uses an **orbital density-based approach**:

1. **Altitude binning** — Objects grouped into 50 km altitude bands
2. **Local density** — Object count within ±50 km of each object's altitude
3. **Orbit class multipliers** — LEO (1.5x), GEO (1.2x) to weight collision probability
4. **Relative velocity** — Combined with density to estimate conjunction frequency
5. **Risk score** — Normalized 0–1 score: Low (< 0.15), Medium (0.15–0.30), High (> 0.30)

**Validation accuracy:** 96.75%

---

## 📱 Mobile Support

The app is fully responsive with:
* Touch controls (pinch-to-zoom, drag-to-rotate, tap-to-select)
* Collapsible panels for small screens
* Mobile-specific object popup
* Compact visual layer toggles

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Guruvendra Pannu**

* GitHub: [@Guruvendra47](https://github.com/Guruvendra47)
* Project: [Space-Debris-Project](https://github.com/Guruvendra47/Space-Debris-Project)

---

## 🙏 Acknowledgments

* **NORAD / USSPACECOM** — For maintaining the satellite catalog and TLE data
* **Celestrak** — For providing free public access to TLE data
* **NOAA SWPC** — For space weather data
* **Three.js** — For the WebGL rendering engine
* **Skyfield** — For orbital mechanics computation
* **Databricks** — For the serverless app hosting platform