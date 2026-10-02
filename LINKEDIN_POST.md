# LinkedIn Post - Space Debris Tracker

---

## POST 1: Project Launch (Long-form)

I built a real-time 3D platform that tracks over 35,000 orbital debris objects and satellites around Earth -- and predicts collision risk using machine learning with 96.75% accuracy.

The problem is real. Over 34,000 objects larger than 10 cm are orbiting Earth right now. Each one threatens active satellites, the International Space Station, and future missions. The Kessler Syndrome -- a cascading collision scenario where debris creates more debris -- is not theoretical. We are approaching those thresholds today.

So I built the Space Debris Tracker.

WHAT IT DOES:

- Renders 35,037 tracked objects in real-time on an interactive 3D Earth globe
- Computes live satellite positions using SGP4/SDP4 orbital propagation (powered by NORAD TLE data from Celestrak)
- Filters by orbital regime (LEO, MEO, GEO, HEO), object type (payload, rocket body, debris), and country
- Runs a density-based ML model that scores collision risk for every object and classifies it as Low, Medium, or High risk
- Extends beyond Earth -- includes orbital data for the Moon, Mars, and Sun
- Works on mobile with touch-optimized controls and responsive design

TECH STACK:

- Databricks Apps (serverless hosting and compute)
- Flask + Gunicorn (backend API and TLE data fetching)
- Three.js (WebGL 3D globe, satellite markers, orbit visualization)
- Skyfield / SGP4-SDP4 (orbital physics and satellite position computation)
- Chart.js (analytics dashboard with density profiles and risk distributions)
- Web Workers (background orbit computation to keep UI at 60 FPS)
- Python ML pipeline (pandas, scikit-learn, numpy)

KEY FINDINGS FROM THE ANALYSIS:

- Low Earth Orbit (400-2,000 km) contains 81% of all tracked debris -- the most congested orbital shell
- The 700-900 km altitude band is the single most crowded region, driven by the 2009 Iridium-Cosmos collision and 2007 Chinese ASAT test
- Over 325 billion USD in satellite assets are currently at risk from orbital debris collisions
- The ML model identifies the top 100 highest-risk objects that operators should prioritize for conjunction monitoring

DEPLOYED ON THREE PLATFORMS:

- Databricks Apps: https://space-debris-tracker-7474652642146548.aws.databricksapps.com
- Vercel: https://orbital-intelligence-platform-ctpvrirrb-guruvendra27-2443.vercel.app
- GitHub Pages: https://space-debris.com

OPEN SOURCE: https://github.com/Guruvendra47/Space-Debris-Project

The repository includes 3 comprehensive technical reports (project report, ML model evaluation, and data analysis), full documentation, and a contributing guide for collaborators.

This project demonstrates that complex space situational awareness can be built with open-source tools and public data. No proprietary software. No restricted APIs. Just Python, JavaScript, and NORAD's freely available catalog.

If you work in space operations, data engineering, or ML -- I would love to hear your feedback.

#SpaceDebris #DataEngineering #MachineLearning #Databricks #Threejs #SpaceTech #OrbitalMechanics #Python #Flask #WebGL #OpenSource #SatelliteTracking #SpaceSituationalAwareness #KesslerSyndrome

---

## POST 2: Short Version (Quick Share)

Over 34,000 pieces of space debris are orbiting Earth right now.

I built a real-time 3D tracker that visualizes 35,037 of them and predicts collision risk using ML with 96.75% accuracy.

Built with Databricks Apps, Three.js, Flask, Skyfield, and Python ML.

Live demo: https://orbital-intelligence-platform-ctpvrirrb-guruvendra27-2443.vercel.app

Open source: https://github.com/Guruvendra47/Space-Debris-Project

#SpaceDebris #MachineLearning #Databricks #Threejs #DataEngineering #OpenSource #SpaceTech

---

## POST 3: Technical Deep-Dive (For Engineering Audience)

How do you render 35,000+ satellites on a 3D globe at 60 FPS while computing real-time orbital positions?

Here is what I built and the engineering challenges I solved:

THE PROBLEM
- Fetch TLE (Two-Line Element) data from NORAD/Celestrak
- Propagate 35,037 satellite positions in real-time using SGP4/SDP4
- Render all objects on a Three.js WebGL globe without dropping frames
- Score collision risk with a density-based ML model
- Make it work on mobile devices

THE ARCHITECTURE

Backend (Flask + Skyfield):
- Fetches latest TLE data from Celestrak on startup
- Propagates satellite positions using SGP4 algorithms
- Serves JSON API with position data for all 35,037 objects
- Response latency under 500ms

Frontend (Three.js + Web Workers):
- WebGL globe with Earth texture and atmosphere shader
- Each object rendered as a 3D marker color-coded by type and risk
- Orbital computation offloaded to Web Worker to prevent UI blocking
- Filter system supports orbital shell, object type, and country
- Touch-optimized controls for mobile (pinch-to-zoom, drag-to-rotate)

ML Pipeline (Python):
- Density-based collision risk scoring using orbital neighborhood analysis
- Features: altitude, inclination, eccentricity, local object density, relative velocity
- 96.75% validation accuracy across 5-fold cross-validation
- Classifies objects as Low, Medium, or High collision risk
- Identifies top 100 priority objects for conjunction monitoring

KEY ENGINEERING CHALLENGES SOLVED:

1. Performance: 35,037 markers at 60 FPS -- solved with Web Workers + instanced rendering
2. TLE freshness: Auto-refresh from Celestrak with fallback to cached data
3. Mobile optimization: Responsive layout down to 320px width, touch controls
4. Coordinate transforms: ECI to ECEF to lat/lon/alt for globe rendering
5. Filter state management: Preserved across celestial body switching (Earth/Moon/Mars)
6. Marker selection: Prevented UI control clicks from triggering object selection

DEPLOYED ON:
- Databricks Apps (serverless): https://space-debris-tracker-7474652642146548.aws.databricksapps.com
- Vercel: https://orbital-intelligence-platform-ctpvrirrb-guruvendra27-2443.vercel.app
- GitHub Pages: https://space-debris.com

Full source code, 3 technical reports, and documentation: https://github.com/Guruvendra47/Space-Debris-Project

#DataEngineering #MachineLearning #WebGL #Threejs #Python #Flask #Databricks #SpaceTech #SoftwareEngineering #OpenSource #RealTimeRendering #SpaceSituationalAwareness

---

## POST 4: Story-Driven (Personal Journey)

I started this project with one question: can an open-source tool make space debris accessible to everyone?

The answer turned out to be yes.

Space debris is one of the most underappreciated challenges of our time. Over 34,000 objects larger than 10 cm are orbiting Earth. The Kessler Syndrome -- where cascading collisions make entire orbital shells unusable -- is approaching. Satellite infrastructure worth 325 billion USD is at risk.

But most tools for tracking this data are proprietary, expensive, or locked behind specialized software like STK and GMAT.

So I built the Space Debris Tracker -- a real-time 3D visualization platform that:
- Tracks 35,037 objects using NORAD TLE data and SGP4 orbital propagation
- Predicts collision risk with a 96.75% accurate ML model
- Renders everything on an interactive 3D globe at 60 FPS
- Works on desktop and mobile
- Extends to the Moon, Mars, and Sun

No proprietary tools. No restricted APIs. Just Python, JavaScript, Skyfield, Three.js, and public data from NORAD.

The project includes 3 full technical reports, comprehensive documentation, and is fully open source.

Live demo: https://orbital-intelligence-platform-ctpvrirrb-guruvendra27-2443.vercel.app
Source code: https://github.com/Guruvendra47/Space-Debris-Project

If you are passionate about space, data engineering, or machine learning -- check it out and let me know what you think.

#SpaceDebris #OpenSource #DataEngineering #MachineLearning #SpaceTech #Databricks #Python #Threejs #KesslerSyndrome #SatelliteTracking
