from nicegui import ui
#from services.flights import load_flights_csv

@ui.page('/')
def index():
    ui.label('Upload your CSV')

    def on_upload(e):
        #df = load_flights_csv('/path/to/saved.csv')
        #ui.navigate.to('/dashboard')
        pass

    #ui.upload(on_upload=on_upload)

@ui.page('/dashboard')
def dashboard():
    #df = ...  
    #build_dashboard(df)
    pass

ui.run()