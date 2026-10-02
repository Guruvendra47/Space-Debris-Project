# Raw Data

This directory contains the original satellite and debris tracking data before processing.

## Files

### space_debris_raw.csv
Original dataset sourced from NORAD Two-Line Element (TLE) catalogs via Celestrak. Contains orbital parameters for tracked space objects including satellites, rocket bodies, and debris.

### space_debris_cleaned.csv
Cleaned version of the raw data with:
- Removed duplicate entries
- Standardized country codes
- Validated orbital parameters
- Filled missing object classifications

This cleaned data is used as input for the ML collision risk model and processed JSON generation for the web application.

## Data Fields

Key fields in both CSV files include:
- **Name** - Object identifier
- **ObjectType** - Classification (Payload, Rocket Body, Debris, Unknown)
- **Owner** - Operating country or organization
- **Perigee / Apogee** - Orbital altitude range (km)
- **Inclination** - Orbital tilt relative to equator (degrees)
- **Period** - Orbital period (minutes)
- **LaunchDate** - Date of launch
- **DecayDate** - Date of re-entry (if applicable)

## Data Sources

- **NORAD** - North American Aerospace Defense Command
- **USSPACECOM** - United States Space Command
- **Celestrak** - Public TLE data distribution (https://celestrak.org/)
