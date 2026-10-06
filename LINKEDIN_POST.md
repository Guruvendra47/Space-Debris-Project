I built a real-time 3D platform that tracks over 35,000 orbital debris objects and satellites around Earth and predicts collision risk using machine learning with 96.75% accuracy.

The problem is real. Over 34,000 objects larger than 10 cm are orbiting Earth right now. Each one threatens active satellites, the International Space Station, and future missions. The Kessler Syndrome a cascading collision scenario where debris creates more debris is not theoretical. We are approaching those thresholds today. Over 325 billion USD in satellite assets are at risk.

So I built the Space Debris Tracker.

WHAT IT DOES:

- Renders 35,037 tracked objects in real-time on an interactive 3D Earth globe at 60 FPS
- Computes live satellite positions using SGP4/SDP4 orbital propagation powered by NORAD TLE data from Celestrak
- Filters by orbital regime (LEO, MEO, GEO, HEO), object type, and country
- ML model scores collision risk for every object as Low, Medium, High, or Critical
- Extends to Moon, Mars, and Sun orbital data
- Works on mobile with touch-optimized controls

TECH STACK: Databricks Apps, Flask, Three.js, Skyfield, Chart.js, Python ML (pandas, scikit-learn, numpy)

KEY FINDINGS:

- LEO (400-2,000 km) contains 81% of all tracked debris, the most congested orbital shell
- 700-900 km band is the most crowded region, driven by the 2009 Iridium-Cosmos collision and 2007 Chinese ASAT test
- Of 35,037 objects: 4,554 Low risk, 1,567 Medium, 20 High, 28,896 Critical

LIVE DEMO: https://orbital-intelligence-platform-ctpvrirrb-guruvendra27-2443.vercel.app

OPEN SOURCE: https://github.com/Guruvendra47/Space-Debris-Project

Includes 3 technical reports, full documentation, and contributing guide. Built with open-source tools and public data. No proprietary software. Just Python, JavaScript, and NORAD's catalog.

If you work in space operations, data engineering, or ML I would love to hear your feedback.

#SpaceDebris #DataEngineering #MachineLearning #Databricks #Threejs #SpaceTech #OrbitalMechanics #Python #Flask #WebGL #OpenSource #SatelliteTracking #SpaceSituationalAwareness #KesslerSyndrome #IBM #NASA #SpaceX
