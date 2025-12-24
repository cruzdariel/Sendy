from nicegui import ui
#from services.flights import compute_metrics

def build_dashboard(df):
    #metrics = compute_metrics(df)

    with ui.row():
        #ui.card().classes("p-4").content(ui.label(f"Flights: {metrics.total_flights}"))
        #ui.card().classes("p-4").content(ui.label(f"Distance: {metrics.total_distance_mi:,.0f} mi"))
        pass

