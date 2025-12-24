from nicegui import ui
import pandas as pd
from math import radians, cos, sin, asin, sqrt
from collections import Counter
import plotly.graph_objects as go

# Global variables to store data
airports_df = None
flights_df = None
flight_stats = {}


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


def load_airports():
    """Load airport data from CSV"""
    global airports_df
    try:
        airports_df = pd.read_csv('data/Airports.csv')
        print(f"Loaded {len(airports_df)} airports")
    except Exception as e:
        print(f"Error loading airports: {e}")


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
    try:
        diff = landing - takeoff
        return diff.total_seconds() / 3600
    except:
        return 0


def calculate_delay(scheduled, actual):
    """Calculate delay in hours"""
    if scheduled is None or actual is None:
        return 0
    try:
        diff = actual - scheduled
        return max(0, diff.total_seconds() / 3600)
    except:
        return 0


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


def analyze_flights(df):
    """Analyze flight data and calculate statistics"""
    global flight_stats

    stats = {}

    # Total flights
    stats['total_flights'] = len(df)

    # Parse datetime columns
    df['Takeoff_Actual'] = df['Take off (Actual)'].apply(parse_datetime)
    df['Landing_Actual'] = df['Landing (Actual)'].apply(parse_datetime)
    df['Gate_Departure_Scheduled'] = df['Gate Departure (Scheduled)'].apply(parse_datetime)
    df['Gate_Departure_Actual'] = df['Gate Departure (Actual)'].apply(parse_datetime)
    df['Gate_Arrival_Scheduled'] = df['Gate Arrival (Scheduled)'].apply(parse_datetime)
    df['Gate_Arrival_Actual'] = df['Gate Arrival (Actual)'].apply(parse_datetime)

    # Calculate distances and flight times
    total_distance = 0
    total_flight_time = 0
    total_delay = 0
    routes = []

    for _, row in df.iterrows():
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

    stats['total_distance'] = round(total_distance, 2)
    stats['total_flight_time'] = round(total_flight_time, 2)
    stats['total_delay'] = round(total_delay, 2)

    # Unique airports
    airports_visited = set()
    for airport in df['From'].dropna():
        airports_visited.add(airport)
    for airport in df['To'].dropna():
        airports_visited.add(airport)
    stats['airports_visited'] = sorted(list(airports_visited))
    stats['total_airports'] = len(airports_visited)

    # Airlines
    airlines = df['Airline'].dropna().value_counts()
    stats['airlines'] = airlines.to_dict()
    stats['total_airlines'] = len(airlines)
    stats['top_airline'] = airlines.index[0] if len(airlines) > 0 else 'N/A'

    # Aircraft types
    aircraft = df['Aircraft Type Name'].dropna().value_counts()
    stats['aircraft_types'] = aircraft.to_dict()
    stats['most_flown_aircraft'] = aircraft.index[0] if len(aircraft) > 0 else 'N/A'

    # Top routes
    route_counts = Counter()
    for _, row in df.iterrows():
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

    # Store routes for map
    stats['routes'] = routes
    stats['flights_data'] = df

    flight_stats = stats
    return stats


def upload_csv(e):
    """Handle CSV file upload"""
    global flights_df, flight_stats

    if e.content:
        try:
            # Read CSV from uploaded content
            from io import StringIO
            content = e.content.read().decode('utf-8')
            flights_df = pd.read_csv(StringIO(content))

            # Analyze flights
            analyze_flights(flights_df)

            # Update UI with statistics
            update_dashboard()

            ui.notify(f'Successfully loaded {len(flights_df)} flights!', type='positive')
        except Exception as ex:
            ui.notify(f'Error loading CSV: {str(ex)}', type='negative')


def update_dashboard():
    """Update dashboard with flight statistics"""
    dashboard_container.clear()

    with dashboard_container:
        if not flight_stats:
            ui.label('No data loaded. Please upload a CSV file.').classes('text-xl')
            return

        # Statistics cards
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1'):
                ui.label('Total Flights').classes('text-h6')
                ui.label(str(flight_stats.get('total_flights', 0))).classes('text-h4 text-primary')

            with ui.card().classes('flex-1'):
                ui.label('Distance Traveled').classes('text-h6')
                ui.label(f"{flight_stats.get('total_distance', 0):,.0f} miles").classes('text-h4 text-primary')

            with ui.card().classes('flex-1'):
                ui.label('Flight Time').classes('text-h6')
                ui.label(f"{flight_stats.get('total_flight_time', 0):,.1f} hours").classes('text-h4 text-primary')

            with ui.card().classes('flex-1'):
                ui.label('Delay Time').classes('text-h6')
                ui.label(f"{flight_stats.get('total_delay', 0):,.1f} hours").classes('text-h4 text-primary')

        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1'):
                ui.label('Airports Visited').classes('text-h6')
                ui.label(str(flight_stats.get('total_airports', 0))).classes('text-h4 text-primary')

            with ui.card().classes('flex-1'):
                ui.label('Airlines Flown').classes('text-h6')
                ui.label(str(flight_stats.get('total_airlines', 0))).classes('text-h4 text-primary')

            with ui.card().classes('flex-1'):
                ui.label('Countries Visited').classes('text-h6')
                ui.label(str(flight_stats.get('total_countries', 0))).classes('text-h4 text-primary')

            with ui.card().classes('flex-1'):
                ui.label('Most Flown Aircraft').classes('text-h6')
                ui.label(flight_stats.get('most_flown_aircraft', 'N/A')).classes('text-body1 text-primary')

        # Charts section
        ui.separator()
        ui.label('Top Airlines').classes('text-h5 mt-4')

        with ui.row().classes('w-full gap-4'):
            # Top airlines chart
            with ui.card().classes('flex-1'):
                airlines = flight_stats.get('airlines', {})
                if airlines:
                    airline_data = dict(list(airlines.items())[:10])
                    ui.echart({
                        'title': {'text': 'Top 10 Airlines'},
                        'xAxis': {'type': 'category', 'data': list(airline_data.keys())},
                        'yAxis': {'type': 'value'},
                        'series': [{'type': 'bar', 'data': list(airline_data.values())}]
                    }).classes('w-full h-64')

            # Top routes chart
            with ui.card().classes('flex-1'):
                routes = flight_stats.get('top_routes', {})
                if routes:
                    ui.echart({
                        'title': {'text': 'Top 10 Routes'},
                        'xAxis': {'type': 'category', 'data': list(routes.keys())},
                        'yAxis': {'type': 'value'},
                        'series': [{'type': 'bar', 'data': list(routes.values())}]
                    }).classes('w-full h-64')

        # Aircraft types chart
        ui.label('Top Aircraft Types').classes('text-h5 mt-4')
        with ui.card().classes('w-full'):
            aircraft = flight_stats.get('aircraft_types', {})
            if aircraft:
                aircraft_data = dict(list(aircraft.items())[:10])
                ui.echart({
                    'title': {'text': 'Top 10 Aircraft Types'},
                    'xAxis': {'type': 'category', 'data': list(aircraft_data.keys())},
                    'yAxis': {'type': 'value'},
                    'series': [{'type': 'bar', 'data': list(aircraft_data.values())}]
                }).classes('w-full h-64')

        # Flight map
        ui.label('Flight Map').classes('text-h5 mt-4')
        with ui.card().classes('w-full'):
            create_flight_map()


def create_flight_map():
    """Create an interactive flight map using Plotly"""
    routes = flight_stats.get('routes', [])

    if not routes:
        ui.label('No route data available')
        return

    # Prepare data for plotting
    flight_lines = []
    airport_data = {}

    for from_code, to_code, distance in routes:
        from_lat, from_lon = get_airport_coords(from_code)
        to_lat, to_lon = get_airport_coords(to_code)

        if from_lat and from_lon and to_lat and to_lon:
            flight_lines.append({
                'from': from_code,
                'to': to_code,
                'from_lat': from_lat,
                'from_lon': from_lon,
                'to_lat': to_lat,
                'to_lon': to_lon,
                'distance': distance
            })

            # Track airports
            if from_code not in airport_data:
                airport_data[from_code] = {'lat': from_lat, 'lon': from_lon, 'count': 0}
            airport_data[from_code]['count'] += 1

            if to_code not in airport_data:
                airport_data[to_code] = {'lat': to_lat, 'lon': to_lon, 'count': 0}
            airport_data[to_code]['count'] += 1

    if not flight_lines:
        ui.label('Unable to plot routes')
        return

    # Create Plotly figure
    fig = go.Figure()

    # Add flight routes as lines
    for line in flight_lines:
        fig.add_trace(go.Scattergeo(
            lon=[line['from_lon'], line['to_lon']],
            lat=[line['from_lat'], line['to_lat']],
            mode='lines',
            line=dict(width=1, color='rgba(51, 136, 255, 0.5)'),
            hoverinfo='text',
            text=f"{line['from']} → {line['to']}<br>{line['distance']:.0f} miles",
            showlegend=False
        ))

    # Add airport markers
    airport_lats = [data['lat'] for data in airport_data.values()]
    airport_lons = [data['lon'] for data in airport_data.values()]
    airport_names = list(airport_data.keys())
    airport_counts = [data['count'] for data in airport_data.values()]

    fig.add_trace(go.Scattergeo(
        lon=airport_lons,
        lat=airport_lats,
        mode='markers',
        marker=dict(
            size=[min(8 + count * 2, 20) for count in airport_counts],
            color='#ff7800',
            line=dict(width=1, color='white')
        ),
        text=[f"{name}<br>{count} flights" for name, count in zip(airport_names, airport_counts)],
        hoverinfo='text',
        name='Airports'
    ))

    # Update layout
    fig.update_layout(
        title='Flight Routes Map',
        showlegend=False,
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 245, 255)',
            showcountries=True,
            countrycolor='rgb(204, 204, 204)',
        ),
        height=600,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    # Display using plotly in NiceGUI
    ui.plotly(fig).classes('w-full')

    # Add route summary
    ui.label(f'Total unique routes: {len(flight_lines)} | Airports visited: {len(airport_data)}').classes('text-body2 text-grey mt-2')


# Initialize app
@ui.page('/')
def main_page():
    ui.colors(primary='#3b82f6')

    with ui.header().classes('items-center justify-between'):
        ui.label('Flighty Dashboard').classes('text-h4')

    with ui.column().classes('w-full p-4'):
        ui.label('Flight Tracking Dashboard').classes('text-h3')
        ui.label('Upload your Flighty CSV export to visualize your flight history').classes('text-body1 text-grey')

        ui.separator()

        ui.upload(
            label='Upload Flighty CSV',
            on_upload=upload_csv,
            auto_upload=True
        ).classes('mb-4').props('accept=".csv"')

        global dashboard_container
        dashboard_container = ui.column().classes('w-full')

        # Show initial message
        with dashboard_container:
            ui.label('No data loaded. Please upload a CSV file.').classes('text-xl')


# Load airports on startup
load_airports()

# Load default data if available
try:
    flights_df = pd.read_csv('data/FlightyExport.csv')
    flight_stats = analyze_flights(flights_df)
    print(f"Pre-loaded {len(flights_df)} flights")
except Exception as e:
    print(f"No default data loaded: {e}")

ui.run(title='Flighty Dashboard', port=8080)
