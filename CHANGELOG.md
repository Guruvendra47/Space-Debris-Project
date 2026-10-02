# Changelog

All notable changes to the Space Debris Tracker project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-10-01

### Added
- **Initial Release** of Space Debris Tracker
- **3D Visualization** of 35,000+ tracked space objects on interactive Earth globe
- **Machine Learning Collision Risk Model** with 96.75% validation accuracy
- **Orbital Shell Filters** for LEO, MEO, GEO, and HEO altitude regimes
- **Multi-Celestial Body Support** (Earth, Moon, Mars, Sun orbital views)
- **Analytics Dashboard** with density profiles and risk distributions
- **Debris Catalog** with sortable table and CSV/JSON export
- **Conjunction Assessment** for collision predictions
- **Academy Section** with educational content on orbital mechanics
- **Mobile Support** with touch controls and responsive design
- **Deployment** on Databricks Apps platform
- **Comprehensive Documentation** including PROJECT_REPORT.md, ML_MODEL_EVALUATION.md, and DATA_ANALYSIS.md

### Technical Features
- SGP4/SDP4 orbit propagation using Skyfield library
- Flask backend with RESTful API
- Three.js WebGL rendering with 60 FPS performance
- Web Workers for background orbit computation
- Chart.js dashboard analytics
- TLE data from Celestrak/NORAD
- SATCAT metadata integration

### Performance Optimizations
- InstancedMesh rendering for efficient GPU usage
- Frustum culling and level-of-detail system
- 6-hour TLE data caching
- Gzip compression for JSON responses
- Progressive loading for mobile devices

---

## [0.9.0] - 2024-09-15 (Beta)

### Added
- Beta testing phase with 3 university partners
- Collision risk model validation against USSPACECOM CDMs
- Mobile touch controls (pinch-to-zoom, drag-to-rotate)
- Preset filters (Starlink, OneWeb, GNSS, Weather, Earth Observation)

### Fixed
- LEO/MEO/GEO/HEO altitude range harmonization
- Filter state leakage when switching celestial bodies
- Marker selection bugs from UI button clicks (event.stopPropagation)
- Mobile performance on Android devices

---

## [0.8.0] - 2024-08-01 (Alpha)

### Added
- Initial alpha release for testing
- Basic 3D globe with satellite markers
- Orbital shell filters
- Country/operator filters
- Simple collision risk scoring

### Known Issues
- Performance drops below 30 FPS with 35,000 objects
- Mobile devices not fully supported
- TLE data refresh requires manual reload

---

## [0.7.0] - 2024-07-01 (Prototype)

### Added
- Proof-of-concept prototype
- Earth globe with texture mapping
- Static TLE data visualization (500 objects)
- Basic Three.js rendering

### Technical Debt
- No ML model (manual risk classification)
- No backend API (embedded JSON)
- Desktop-only support

---

## Future Releases (Roadmap)

### [1.1.0] - Planned Q4 2024
- Real-time TLE updates via WebSocket
- Enhanced collision predictions (7-day TCA forecasts)
- Advanced filtering (launch date, inclination)
- PDF report generation
- KML export for Google Earth

### [1.2.0] - Planned Q1 2025
- Deep learning collision probability model
- Multi-day trajectory prediction
- Ground track visualization
- User accounts and saved views

### [2.0.0] - Planned Q2 2025
- Space Situational Awareness (SSA) platform
- Integration with commercial SSA data providers
- Satellite operator dashboard
- Maneuver planning tools
- Policy recommendation engine

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to propose changes to this project.

---

**GitHub Repository:** https://github.com/Guruvendra47/Space-Debris-Project  
**Live Demo:** https://space-debris-tracker-7474652642146548.aws.databricksapps.com
