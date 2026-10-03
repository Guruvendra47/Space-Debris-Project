I built a real-time 3D platform that tracks over 35,000 orbital debris objects and satellites around Earth -- and predicts collision risk using machine learning with 96.75% accuracy.

The problem is real. Over 34,000 objects larger than 10 cm are orbiting Earth right now. Each one threatens active satellites, the International Space Station, and future missions. The Kessler Syndrome -- a cascading collision scenario where debris creates more debris -- is not theoretical. We are approaching those thresholds today. Over 325 billion USD in satellite assets are at risk.

So I built the Space Debris Tracker.

WHAT IT DOES:

- Renders 35,037 tracked objects in real-time on an interactive 3D Earth globe at 60 FPS
- Computes live satellite positions using SGP4/SDP4 orbital propagation powered by NORAD TLE data from Celestrak
- Filters by orbital regime (LEO, MEO, GEO, HEO), object type (payload, rocket body, debris), and country
- Runs a density-based ML model that scores collision risk for every object -- classifying them as Low, Medium, High, or Critical risk
- Identifies the top 100 highest-risk objects for conjunction monitoring
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
- Of 35,037 analyzed objects: 4,554 Low risk, 1,567 Medium, 20 High, 28,896 Critical

DEPLOYED ON THREE PLATFORMS:

- Databricks Apps: https://space-debris-tracker-7474652642146548.aws.databricksapps.com
- Vercel: https://orbital-intelligence-platform-ctpvrirrb-guruvendra27-2443.vercel.app
- GitHub Pages: https://space-debris.com

OPEN SOURCE: https://github.com/Guruvendra47/Space-Debris-Project

The repository includes 3 comprehensive technical reports (project report, ML model evaluation, and data analysis), full documentation, and a contributing guide.

This project demonstrates that complex space situational awareness can be built with open-source tools and public data. No proprietary software. No restricted APIs. Just Python, JavaScript, and NORAD's freely available catalog.

If you work in space operations, data engineering, or ML -- I would love to hear your feedback.

#NASA #SpaceX #SpaceDebris #DataEngineering #MachineLearning #SpaceExploration #Databricks #Threejs #SpaceTech #Satellite #OrbitalMechanics #Python #Flask #WebGL #OpenSource #SpaceSituationalAwareness #KesslerSyndrome #Aerospace #DataScience #SpaceIndustry #SatelliteTracking #3DVisualization #SoftwareEngineering #ArtificialIntelligence #Innovation
