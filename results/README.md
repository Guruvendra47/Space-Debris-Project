# Results

This directory contains output files generated from the Space Debris Tracker analysis pipeline.

## Overview

The results folder stores computational outputs, processed datasets, and analysis artifacts that are generated from the Jupyter notebooks and ML model training processes. These files serve as intermediate or final outputs that support the web application and reports.

## Typical Contents

This directory may include:

### ML Model Outputs
* **model_performance.json** - Model accuracy, precision, recall, F1 scores
* **confusion_matrix.csv** - Classification performance breakdown
* **feature_importance.json** - Most influential features in collision risk prediction
* **training_history.json** - Loss and accuracy curves over epochs

### Analysis Results
* **debris_density_by_altitude.csv** - Object count per 50km altitude band
* **high_risk_objects.csv** - Top 100 objects by collision probability
* **orbital_shell_statistics.json** - LEO/MEO/GEO/HEO distribution summary
* **conjunction_events.csv** - Predicted close approaches for next 30 days

### Processed Datasets
* **filtered_tle_data.csv** - TLE data after quality filtering
* **enriched_satcat.csv** - SATCAT catalog with computed risk scores
* **celestial_body_data.json** - Moon/Mars orbital object metadata

### Visualization Data
* **heatmap_data.json** - 2D density matrix for frontend rendering
* **orbit_trajectories.json** - Precomputed orbital paths for key objects
* **time_series_data.json** - Temporal trends (debris growth 2020-2024)

## File Naming Convention

Results files should follow this naming pattern:
```
<analysis-type>_<date>_<version>.ext

Example:
collision_risk_20241001_v2.csv
```

## Usage

Results files are referenced by:
1. The Jupyter notebooks (`Jupyter Notebooks/`) for analysis
2. The Flask backend (`webapp/app.py`) for data serving
3. The reports (`reports/`) for documentation

## Regenerating Results

To regenerate all results:

```bash
cd "Jupyter Notebooks"
# Run the data pipeline notebook
python "Space Debris Tracking Platform.py"

# Run the ML training notebook
python "Space Debris ML Modeling.py"
```

Results will be automatically saved to this directory.

## Gitignore

Large result files (> 10 MB) should be excluded from Git via `.gitignore`. The repository includes processed results under 10 MB for reproducibility.
