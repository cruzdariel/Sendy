from nicegui import ui
from ui_components.cards import stat_card, chart_card
from ui_components.map import create_flight_map


def build_dashboard(stats):
    """Build the complete dashboard with statistics, charts, and map"""

    if not stats:
        ui.label('No data loaded. Please upload a CSV file.').classes('text-xl')
        return

    # Statistics cards
    with ui.row().classes('w-full gap-4'):
        stat_card('Total Flights', stats.get('total_flights', 0))
        stat_card('Distance Traveled', f"{stats.get('total_distance', 0):,.0f} miles")
        stat_card('Flight Time', f"{stats.get('total_flight_time', 0):,.1f} hours")
        stat_card('Delay Time', f"{stats.get('total_delay', 0):,.1f} hours")

    with ui.row().classes('w-full gap-4'):
        stat_card('Airports Visited', stats.get('total_airports', 0))
        stat_card('Airlines Flown', stats.get('total_airlines', 0))
        stat_card('Countries Visited', stats.get('total_countries', 0))
        with ui.card().classes('flex-1'):
            ui.label('Most Flown Aircraft').classes('text-h6')
            ui.label(stats.get('most_flown_aircraft', 'N/A')).classes('text-body1 text-primary')

    # Charts section
    ui.separator()
    ui.label('Top Airlines').classes('text-h5 mt-4')

    with ui.row().classes('w-full gap-4 flex-wrap'):
        airlines = stats.get('airlines', {})
        if airlines:
            airline_data = dict(list(airlines.items())[:10])
            with ui.element().classes('w-full md:flex-1'):
                chart_card('Top 10 Airlines', airline_data)

        # Top routes chart
        routes = stats.get('top_routes', {})
        if routes:
            with ui.element().classes('w-full md:flex-1'):
                chart_card('Top 10 Routes', routes)

    # Aircraft types chart
    ui.label('Top Aircraft Types').classes('text-h5 mt-4')
    with ui.card().classes('w-full'):
        aircraft = stats.get('aircraft_types', {})
        if aircraft:
            aircraft_data = dict(list(aircraft.items())[:10])
            ui.echart({
                'title': {'text': 'Top 10 Aircraft Types'},
                'xAxis': {
                    'type': 'category',
                    'data': list(aircraft_data.keys()),
                    'axisLabel': {
                        'rotate': 45,
                        'interval': 0
                    }
                },
                'yAxis': {'type': 'value'},
                'series': [{
                    'type': 'bar',
                    'data': list(aircraft_data.values()),
                    'label': {
                        'show': True,
                        'position': 'inside',
                        'rotate': 90,
                        'formatter': '{c}'
                    }
                }],
                'grid': {
                    'bottom': '20%',
                    'containLabel': True
                }
            }).classes('w-full').style('min-height: 400px')

    # Flight map
    ui.label('Flight Map').classes('text-h5 mt-4')
    with ui.card().classes('w-full'):
        create_flight_map(stats)