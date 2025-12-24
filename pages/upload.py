# upload page UI
from nicegui import ui
from io import StringIO
import pandas as pd


def build_upload_page(on_upload_callback):
    """
    Build the upload page UI.

    Args:
        on_upload_callback: Function to call when CSV is uploaded
    """
    ui.colors(primary='#3b82f6')

    with ui.header().classes('items-center justify-between'):
        ui.label('Sendy').classes('text-h4')

    with ui.column().classes('w-full items-center justify-center p-8').style('min-height: 70vh'):
        # Hero section
        with ui.column().classes('items-center text-center max-w-2xl'):
            ui.icon('flight', size='4rem').classes('text-primary mb-4')
            ui.label('Share your Flighty stats with friends').classes('text-h2 mb-2')

        # Upload card
        with ui.card().classes('max-w-xl w-full p-8'):
            # Upload component - simplified for NiceGUI 3.x
            async def handle_upload_event(e):
                try:
                    # In NiceGUI 3.x, e.file is a SmallFileUpload object
                    # We need to read its content and convert to StringIO
                    if not hasattr(e, 'file') or not e.file:
                        raise ValueError("No file was uploaded")

                    # Read the file content (async operation)
                    content_bytes = await e.file.read()

                    # Decode to string
                    content_str = content_bytes.decode('utf-8')

                    # Parse CSV from StringIO
                    flights_df = pd.read_csv(StringIO(content_str))

                    # Call the callback
                    on_upload_callback(flights_df)

                except Exception as ex:
                    ui.notify(f'Error loading CSV: {str(ex)}', type='negative')
                    import traceback
                    print(traceback.format_exc())

            ui.upload(
                label='Upload Flighty Export File',
                on_upload=handle_upload_event,
                auto_upload=True
            ).props('accept=".csv"').classes('w-full')

            # Instructions
            with ui.expansion('How to export from Flighty', icon='help').classes('mt-4 w-full'):
                ui.markdown('''
                1. Open the **Flighty** app on your device
                2. Go to **Settings** → **Export Data**
                3. Select **Export to CSV**
                4. Save the file and upload it here
                ''')