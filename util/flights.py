# parse CSV, clean data, compute metrics
import pandas as pd
from collections import Counter
from util.geo import get_airport_coords, get_airport_country, haversine


def filter_flights_by_date_range(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Filter flights by date range.

    Args:
        df: DataFrame with flight data
        start_date: Start date as string (YYYY-MM-DD) or None for no filter
        end_date: End date as string (YYYY-MM-DD) or None for no filter

    Returns:
        Filtered DataFrame
    """
    if start_date is None and end_date is None:
        return df

    # Make sure Date column exists
    if 'Date' not in df.columns:
        return df

    filtered_df = df.copy()

    # Ensure Date column is datetime type
    if not pd.api.types.is_datetime64_any_dtype(filtered_df['Date']):
        filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])

    if start_date and start_date.strip():
        try:
            start = pd.to_datetime(start_date)
            filtered_df = filtered_df[filtered_df['Date'] >= start]
        except Exception as e:
            print(f"Error parsing start date '{start_date}': {e}")

    if end_date and end_date.strip():
        try:
            end = pd.to_datetime(end_date)
            filtered_df = filtered_df[filtered_df['Date'] <= end]
        except Exception as e:
            print(f"Error parsing end date '{end_date}': {e}")

    return filtered_df


def load_flights_csv(path: str) -> pd.DataFrame:
    columns = [
        "Date", "Airline", "Flight", "From", "To", "Canceled", "Diverted To",
        "Gate Departure (Scheduled)", "Gate Departure (Actual)", "Take off (Scheduled)",
        "Take off (Actual)", "Landing (Scheduled)", "Landing (Actual)", "Gate Arrival (Scheduled)",
        "Gate Arrival (Actual)", "Aircraft Type Name", "Tail Number"
    ]
    df = pd.read_csv(path)
    df = df[columns]

    # Date cleaning
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%y")


    return df


def parse_datetime(date_str):
    """Parse datetime from string"""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def calculate_flight_time(takeoff, landing):
    """Calculate flight time in hours"""
    if takeoff is None or landing is None:
        return 0
    # Check for NaN values
    if pd.isna(takeoff) or pd.isna(landing):
        return 0
    try:
        diff = landing - takeoff
        return diff.total_seconds() / 3600
    except:
        return 0


def calculate_delay(scheduled, actual):
    """Calculate delay in hours"""
    if scheduled is None or actual is None:
        return 0
    # Check for NaN values
    if pd.isna(scheduled) or pd.isna(actual):
        return 0
    try:
        diff = actual - scheduled
        return max(0, diff.total_seconds() / 3600)
    except:
        return 0


def compute_metrics(df: pd.DataFrame):
    """Analyze flight data and calculate statistics"""
    stats = {}

    # Count cancelled flights (Canceled column is "TRUE" or "FALSE" as string)
    cancelled_mask = df['Canceled'].astype(str).str.upper() == 'TRUE'
    stats['cancelled_flights'] = int(cancelled_mask.sum())

    # Total flights (excluding cancelled)
    df_active = df[~cancelled_mask].copy()
    stats['total_flights'] = len(df_active)

    # Parse datetime columns (use df_active for metrics)
    df_active['Takeoff_Actual'] = df_active['Take off (Actual)'].apply(parse_datetime)
    df_active['Landing_Actual'] = df_active['Landing (Actual)'].apply(parse_datetime)
    df_active['Gate_Departure_Scheduled'] = df_active['Gate Departure (Scheduled)'].apply(parse_datetime)
    df_active['Gate_Departure_Actual'] = df_active['Gate Departure (Actual)'].apply(parse_datetime)
    df_active['Gate_Arrival_Scheduled'] = df_active['Gate Arrival (Scheduled)'].apply(parse_datetime)
    df_active['Gate_Arrival_Actual'] = df_active['Gate Arrival (Actual)'].apply(parse_datetime)

    # Calculate distances and flight times
    total_distance = 0
    total_flight_time = 0
    total_delay = 0
    routes = []

    for _, row in df_active.iterrows():
        # Get coordinates
        from_lat, from_lon = get_airport_coords(row['From'])
        to_lat, to_lon = get_airport_coords(row['To'])

        if from_lat and from_lon and to_lat and to_lon:
            distance = haversine(from_lon, from_lat, to_lon, to_lat)
            total_distance += distance
            routes.append((row['From'], row['To'], distance))

        # Calculate flight time
        flight_time = calculate_flight_time(row['Takeoff_Actual'], row['Landing_Actual'])
        total_flight_time += flight_time

        # Calculate delays
        delay = calculate_delay(row['Gate_Departure_Scheduled'], row['Gate_Departure_Actual'])
        total_delay += delay

    # Ensure no NaN values in stats
    stats['total_distance'] = round(total_distance, 2) if not pd.isna(total_distance) else 0
    stats['total_flight_time'] = round(total_flight_time, 2) if not pd.isna(total_flight_time) else 0
    stats['total_delay'] = round(total_delay, 2) if not pd.isna(total_delay) else 0

    # Unique airports
    airports_visited = set()
    for airport in df_active['From'].dropna():
        airports_visited.add(airport)
    for airport in df_active['To'].dropna():
        airports_visited.add(airport)
    stats['airports_visited'] = sorted(list(airports_visited))
    stats['total_airports'] = len(airports_visited)

    # Airlines
    airlines = df_active['Airline'].dropna().value_counts()
    stats['airlines'] = airlines.to_dict()
    stats['total_airlines'] = len(airlines)
    stats['top_airline'] = airlines.index[0] if len(airlines) > 0 else 'N/A'

    # Aircraft types
    aircraft = df_active['Aircraft Type Name'].dropna().value_counts()
    stats['aircraft_types'] = aircraft.to_dict()
    stats['most_flown_aircraft'] = aircraft.index[0] if len(aircraft) > 0 else 'N/A'

    # Top routes
    route_counts = Counter()
    for _, row in df_active.iterrows():
        if not pd.isna(row['From']) and not pd.isna(row['To']):
            route = f"{row['From']} → {row['To']}"
            route_counts[route] += 1
    stats['top_routes'] = dict(route_counts.most_common(10))

    # Countries
    countries = set()
    for airport in airports_visited:
        country = get_airport_country(airport)
        if country:
            countries.add(country)
    stats['countries'] = sorted(list(countries))
    stats['total_countries'] = len(countries)

    # Store routes for map and flight data for table (active flights only)
    stats['routes'] = routes
    stats['flights_data'] = df_active

    return stats