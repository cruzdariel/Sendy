# Flighty Dashboard

A web application built with Python and NiceGUI to visualize flight data exported from the Flighty app.

## Features

- **Flight Statistics**:
  - Total flights taken
  - Total distance traveled (in miles)
  - Total flight time (in hours)
  - Hours lost from delays
  - Number of airports visited
  - Number of airlines flown on
  - Number of countries visited
  - Most frequently flown aircraft type

- **Visualizations**:
  - Interactive flight map showing all routes
  - Top 10 airlines chart
  - Top 10 routes chart
  - Top 10 aircraft types chart

- **CSV Upload**: Upload any Flighty export CSV to analyze your flight history

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have your data files in the `data/` directory:
   - `data/Airports.csv` - Airport information with coordinates
   - `data/FlightyExport.csv` - Your Flighty flight data (optional, can upload via UI)

## Usage

Run the application:
```bash
python app.py
```

The dashboard will be available at `http://localhost:8080`

## Data Format

The application expects CSV files with the following columns:
- Date
- Airline
- Flight
- From (airport IATA code)
- To (airport IATA code)
- Gate Departure (Scheduled)
- Gate Departure (Actual)
- Take off (Scheduled)
- Take off (Actual)
- Landing (Scheduled)
- Landing (Actual)
- Gate Arrival (Scheduled)
- Gate Arrival (Actual)
- Aircraft Type Name
- Plus additional optional fields

## How It Works

1. **Distance Calculation**: Uses the Haversine formula to calculate great circle distances between airports
2. **Flight Time**: Calculates based on actual takeoff and landing times
3. **Delays**: Compares scheduled vs actual gate departure times
4. **Mapping**: Uses Leaflet.js to render interactive flight routes on a world map
5. **Charts**: Uses ECharts (via NiceGUI) for interactive data visualizations

## Requirements

- Python 3.8+
- NiceGUI 1.4.0+
- Pandas 2.0.0+
- NumPy 1.24.0+
