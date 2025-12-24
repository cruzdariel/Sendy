# map component wrapper
from nicegui import ui
import plotly.graph_objects as go
from util.geo import get_airport_coords


def create_flight_map(stats):
    """Create an interactive flight map using Plotly"""
    routes = stats.get('routes', [])

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
            hoverinfo='skip',  # Don't show tooltips for routes
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
