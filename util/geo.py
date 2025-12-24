# distance calc, airport coords lookup
import pandas as pd
from math import radians, cos, sin, asin, sqrt

# Global variable to store airport data
airports_df = None


def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points on earth (specified in decimal degrees)"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    miles = km * 0.621371
    return miles


def load_airports(csv_path='data/airports.csv'):
    """Load airport data from CSV"""
    global airports_df
    try:
        airports_df = pd.read_csv(csv_path)
        print(f"Loaded {len(airports_df)} airports")
    except Exception as e:
        print(f"Error loading airports: {e}")


def get_airport_coords(airport_code):
    """Get coordinates for an airport by IATA code"""
    if airports_df is None or pd.isna(airport_code):
        return None, None

    airport = airports_df[airports_df['iata_code'] == airport_code]
    if len(airport) == 0:
        return None, None

    return airport.iloc[0]['latitude_deg'], airport.iloc[0]['longitude_deg']


def get_airport_country(airport_code):
    """Get country for an airport by IATA code"""
    if airports_df is None or pd.isna(airport_code):
        return None

    airport = airports_df[airports_df['iata_code'] == airport_code]
    if len(airport) == 0:
        return None

    return airport.iloc[0]['iso_country']
