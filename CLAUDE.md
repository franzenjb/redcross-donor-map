# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

American Red Cross Donor Map - An interactive data visualization platform showing donor locations and contribution patterns across the United States. The application features both a standalone HTML/JavaScript implementation and a Flask backend for API-driven visualizations.

## Architecture

### Dual Implementation Structure
The project has two parallel implementations:

1. **Static Frontend (index.html)** - Primary implementation
   - Self-contained single-page application
   - Direct CSV parsing with PapaParse
   - Multiple map visualization types (Leaflet clusters, Plotly heatmaps, choropleth, point maps)
   - Advanced analytics dashboard with 5 specialized charts for development officers
   - No server required - can be served via GitHub Pages or any static host

2. **Flask Backend (app.py)** - API-driven alternative
   - REST API endpoints for filtered data
   - Server-side data processing with pandas
   - Plotly-based visualizations
   - Template rendering via Flask

### Key Data Flow
- Donor data stored in `data/donors.csv` (10,000+ records)
- Contains geocoded locations (X/Y coordinates), gift amounts, donor IDs
- Data filtered by state, city, gift category, and minimum gift amount
- Visualizations update dynamically based on filter selections

## Development Commands

### Static Frontend Development
```bash
# Serve locally with Python
python3 -m http.server 8000

# Or use any static file server
npx http-server -p 8000
```

### Flask Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py  # Runs on port 8080

# Production deployment
gunicorn app:app --bind 0.0.0.0:8080
```

### Deployment
```bash
# Deploy to GitHub Pages (static version only)
git add -A
git commit -m "Your commit message"
git push origin main

# GitHub Pages URL
https://franzenjb.github.io/redcross-donor-map/
```

## Data Processing Details

### CSV Structure
The `donors.csv` file contains columns:
- `X`, `Y`: Longitude and latitude coordinates
- ` Gift $ `: Donation amount (note the spaces in column name)
- `State`, `Region Abbreviation`: State codes
- `City`, `City.1`, `ARC Best City`: City names (multiple fallback columns)
- `Donor #`: Unique donor identifier

### Gift Categories
Donations are categorized into ranges:
- $5K, $5K-7.5K, $7.5K-10K, $10K-15K, $15K-25K, $25K-50K, $50K-100K, >$100K

### Data Filtering
The application filters out:
- Non-continental US locations (Alaska, Hawaii, territories)
- Invalid coordinates or gift amounts
- Locations outside reasonable US bounds (lat: 24-50, lon: -125 to -66)

## Advanced Analytics Dashboard

The dashboard includes 5 specialized visualizations:

1. **Per Capita Efficiency Chart**: Horizontal bar chart showing donations per capita by state
2. **Opportunity Matrix**: Bubble chart plotting average gift size vs donor count
3. **Velocity Radar**: Multi-metric comparison across 6 performance dimensions
4. **Wealth Gap Analysis**: Compares actual vs potential donations based on state wealth indices
5. **Concentration Treemap**: Hierarchical view of donation concentration by state and top donors

Each chart includes:
- State population data (2023 estimates)
- Wealth index calculations (relative to national average)
- Interactive Plotly visualizations
- Key insights and recommendations for development officers

## Map Visualization Types

1. **Leaflet Clusters**: Interactive marker clustering with zoom-based aggregation
2. **Mapbox Points**: Individual donor points with size/color coding
3. **Heatmap**: Density visualization showing donation concentration
4. **Choropleth**: State-level aggregation showing total donations by state

## Color Scheme

The application uses American Red Cross brand colors:
- Primary Red: #ED1B2E
- Secondary Red: #B31E29
- Dark Red: #8B1A1E
- Gray: #6D6E70
- Light Gray: #D7D7D8

## Theme Support

The application supports light/dark themes:
- Theme preference stored in localStorage
- Automatic map style switching (carto-positron/carto-darkmatter)
- CSS variables for theme-aware styling

## Important Implementation Notes

### Coordinate System
- Uses standard WGS84 coordinates (X=longitude, Y=latitude)
- Leaflet expects [latitude, longitude] order
- Plotly Mapbox expects separate lon/lat arrays

### Performance Considerations
- Large dataset (10,000+ points) requires clustering for Leaflet
- Heatmap intensity is adjustable (radius 5-50)
- Charts limited to top 15-20 items for readability

### Browser Compatibility
- Requires modern browser with ES6 support
- Plotly.js and Leaflet loaded from CDN
- No build process or transpilation needed for static version