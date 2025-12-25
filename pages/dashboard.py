from nicegui import ui
from ui_components.cards import stat_card, chart_card
from ui_components.map import create_flight_map


def build_dashboard(stats, show_flight_list=True):
    """Build the complete dashboard with statistics, charts, and map

    Args:
        stats: Dictionary of flight statistics
        show_flight_list: Whether to display the flight details table (default: True)
    """

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
        stat_card('Cancelled Flights', stats.get('cancelled_flights', 0))
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
            }).classes('w-full').style('min-height: 500px')

    # Flight map
    ui.label('Flight Map').classes('text-h5 mt-4')
    with ui.card().classes('w-full'):
        create_flight_map(stats)

    # Flight details table (conditionally shown)
    if show_flight_list:
        ui.label('Flight Details').classes('text-h5 mt-4')
        with ui.card().classes('w-full'):
            flights_df = stats.get('flights_data')
            if flights_df is not None and not flights_df.empty:
                # Prepare table data
                import pandas as pd
                table_data = flights_df[['Date', 'Airline', 'Flight', 'From', 'To']].copy()

                # Safely convert Date column to string format
                try:
                    # Ensure it's datetime first, then format
                    table_data['Date'] = pd.to_datetime(table_data['Date']).dt.strftime('%Y-%m-%d')
                except:
                    # Fallback to simple string conversion if datetime conversion fails
                    table_data['Date'] = table_data['Date'].astype(str)

                # Create unique row IDs for proper pagination
                table_data['row_id'] = range(len(table_data))

                # Create table with pagination
                columns = [
                    {'name': 'date', 'label': 'Date', 'field': 'Date', 'sortable': True, 'align': 'left'},
                    {'name': 'airline', 'label': 'Airline', 'field': 'Airline', 'sortable': True, 'align': 'left'},
                    {'name': 'flight', 'label': 'Flight Number', 'field': 'Flight', 'sortable': True, 'align': 'left'},
                    {'name': 'origin', 'label': 'Origin', 'field': 'From', 'sortable': True, 'align': 'center'},
                    {'name': 'destination', 'label': 'Destination', 'field': 'To', 'sortable': True, 'align': 'center'},
                ]

                rows = table_data.to_dict('records')

                ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='row_id',
                    pagination={'rowsPerPage': 10, 'sortBy': 'date', 'descending': True}
                ).classes('w-full')
            else:
                ui.label('No flight data available')