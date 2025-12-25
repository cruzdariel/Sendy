from nicegui import ui, app
from io import StringIO
import pandas as pd
from util.flights import load_flights_csv, compute_metrics, filter_flights_by_date_range
from util.geo import load_airports
from util.share import create_share, load_shared_dataset, get_share_url, validate_share_id
from util.storage import save_dataset
from pages.dashboard import build_dashboard
from pages.upload import build_upload_page

# In-memory storage for session data (avoids JSON serialization issues)
session_data = {}
dashboard_container = None

app.add_static_files('/static', 'static')

ui.add_head_html("""
<meta property="og:title" content="Sendy">
<meta property="og:description" content="An indie tool to share your Flighty stats with friends and family.">
<meta property="og:image" content="https://sendy.dariel.us/cover.png">
<meta property="og:url" content="https://sendy.dariel.us">
<meta property="og:type" content="website">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Sendy">
<meta name="twitter:description" content="An indie tool to share your Flighty stats with friends and family.">
<meta name="twitter:image" content="https://sendy.dariel.us/cover.png">
""", shared=True)

def update_dashboard_view():
    """Update dashboard with filtered data based on date range"""
    global dashboard_container

    if dashboard_container is None:
        return

    # Get original data
    flights_df_original = session_data.get('flights_df_original')
    if flights_df_original is None:
        return

    # Get date range from session
    start_date = session_data.get('filter_start_date')
    end_date = session_data.get('filter_end_date')

    # Filter data
    filtered_df = filter_flights_by_date_range(flights_df_original, start_date, end_date)

    # Recompute metrics
    flight_stats = compute_metrics(filtered_df)

    # Update session data with filtered results
    session_data['flights_df'] = filtered_df
    session_data['flight_stats'] = flight_stats

    # Rebuild dashboard
    dashboard_container.clear()
    with dashboard_container:
        build_dashboard(flight_stats)


def create_share_link():
    """Create a shareable link for the current dataset"""
    # Get filtered data from session storage
    flights_df = session_data.get('flights_df')
    flight_stats = session_data.get('flight_stats')

    if flights_df is None or not flight_stats:
        ui.notify('No data to share. Please upload a CSV first.', type='warning')
        return

    # Show dialog to get name and create share
    with ui.dialog() as name_dialog, ui.card() as dialog_card:
        # Container for dialog content that we can update
        content_container = ui.column().classes('w-full')

        def show_name_input():
            """Show the name input form"""
            content_container.clear()
            with content_container:
                ui.label('Share Your Flight Data').classes('text-h5')
                ui.separator()

                # Show date range info if filtered
                start_date = session_data.get('filter_start_date')
                end_date = session_data.get('filter_end_date')
                if start_date or end_date:
                    date_info = f"Date range: {start_date or 'All'} to {end_date or 'All'}"
                    ui.label(date_info).classes('text-body2 text-grey mt-2')

                ui.label('Enter your name (optional):').classes('mt-4')
                name_input = ui.input(placeholder='e.g., Dariel').classes('w-full')

                def generate_share():
                    try:
                        owner_name = name_input.value.strip() if name_input.value else None

                        # Get date range if filtered
                        date_range = None
                        start_date = session_data.get('filter_start_date')
                        end_date = session_data.get('filter_end_date')
                        if start_date or end_date:
                            date_range = {
                                'start': start_date,
                                'end': end_date
                            }

                        # Create share with owner name and date range
                        share_id = create_share(flights_df, flight_stats, expiry_days=30, owner_name=owner_name, date_range=date_range)
                        if share_id:
                            share_url = get_share_url(share_id)
                            ui.notify('Share link created!', type='positive')

                            # Update dialog content to show success
                            show_success(share_url, owner_name, date_range)
                        else:
                            ui.notify('Failed to create share link', type='negative')
                    except Exception as ex:
                        ui.notify(f'Error creating share: {str(ex)}', type='negative')
                        import traceback
                        print(traceback.format_exc())

                with ui.row().classes('w-full gap-2 mt-4'):
                    ui.button('Generate Share Link', icon='share', on_click=generate_share).props('color=primary')
                    ui.button('Cancel', on_click=name_dialog.close).props('flat')

        def show_success(share_url, owner_name, date_range):
            """Show the success screen with share link"""
            content_container.clear()
            with content_container:
                ui.label('Share Link Created!').classes('text-h5')
                ui.separator().classes('my-4')

                if owner_name:
                    ui.label(f"Shared as: {owner_name}'s Flights").classes('text-body1 text-primary mb-2')

                if date_range:
                    range_text = f"Date range: {date_range.get('start') or 'Beginning'} to {date_range.get('end') or 'End'}"
                    ui.label(range_text).classes('text-body2 text-grey mb-2')

                ui.label('Your shareable link (expires in 30 days):').classes('text-body2 mt-4')
                with ui.row().classes('w-full items-center gap-2 mt-2'):
                    ui.input(value=share_url).classes('flex-1').props('readonly')
                    ui.button('Copy', icon='content_copy', on_click=lambda: (
                        ui.run_javascript(f'navigator.clipboard.writeText("{share_url}")'),
                        ui.notify('Link copied to clipboard!', type='positive')
                    )).props('dense')
                ui.button('Close', on_click=lambda: name_dialog.close()).classes('mt-4')

        # Start with name input form
        show_name_input()

    name_dialog.open()


@ui.page('/')
def index():
    """Upload page - initial landing page"""

    def handle_upload(flights_df: pd.DataFrame):
        """Handle successful CSV upload"""
        try:
            # Compute metrics
            flight_stats = compute_metrics(flights_df)

            # Store in session data (simple dict, no persistence)
            session_data['flights_df_original'] = flights_df  # Keep original unfiltered data
            session_data['flights_df'] = flights_df
            session_data['flight_stats'] = flight_stats
            session_data['filter_start_date'] = None  # Reset filters
            session_data['filter_end_date'] = None

            ui.notify(f'Successfully loaded {len(flights_df)} flights!', type='positive')

            # Navigate to dashboard
            ui.navigate.to('/dashboard')

        except Exception as ex:
            ui.notify(f'Error processing data: {str(ex)}', type='negative')
            import traceback
            print(traceback.format_exc())

    # Build the upload page
    build_upload_page(on_upload_callback=handle_upload)


@ui.page('/dashboard')
def dashboard():
    """Dashboard page - shows flight statistics and visualizations"""
    global dashboard_container

    ui.colors(primary='#3b82f6')

    # Get data from session storage
    flight_stats = session_data.get('flight_stats')
    flights_df = session_data.get('flights_df_original')

    with ui.header().classes('items-center justify-between'):
        ui.label('Sendy').classes('text-h4 font-bold')
        with ui.row().classes('gap-2'):
            ui.button('Upload New', icon='upload', on_click=lambda: ui.navigate.to('/')).props('flat text-color=white')
            ui.button('Share', icon='share', on_click=create_share_link).props('flat text-color=white')

    with ui.column().classes('w-full p-4'):
        if not flight_stats:
            # No data loaded - redirect to upload page
            ui.label('No data loaded').classes('text-h4')
            ui.label('Please upload a CSV file first.').classes('text-body1 text-grey mt-2')
            ui.button('Go to Upload', icon='upload', on_click=lambda: ui.navigate.to('/')).classes('mt-4')
            return

        # Show dashboard header
        ui.label(f'Analyzing {flight_stats.get("total_flights", 0)} flights').classes('text-body1 text-grey')

        # Date range filter - compact version
        if flights_df is not None and 'Date' in flights_df.columns:
            with ui.expansion('Filter by Date Range', icon='filter_alt').classes('w-full mb-4'):
                with ui.row().classes('w-full gap-2 items-center p-2'):
                    ui.label('From:').classes('text-sm')
                    start_input = ui.input(label='Start Date', placeholder='YYYY-MM-DD').classes('w-40').props('dense')

                    ui.label('To:').classes('text-sm')
                    end_input = ui.input(label='End Date', placeholder='YYYY-MM-DD').classes('w-40').props('dense')

                    def apply_filter():
                        try:
                            session_data['filter_start_date'] = start_input.value if start_input.value else None
                            session_data['filter_end_date'] = end_input.value if end_input.value else None
                            update_dashboard_view()
                            ui.notify('Date filter applied', type='positive')
                        except Exception as e:
                            ui.notify(f'Error applying filter: {str(e)}', type='negative')

                    def reset_filter():
                        start_input.value = ''
                        end_input.value = ''
                        session_data['filter_start_date'] = None
                        session_data['filter_end_date'] = None
                        update_dashboard_view()
                        ui.notify('Filter reset', type='info')

                    ui.button('Apply', icon='check', on_click=apply_filter).props('dense color=primary size=sm')
                    ui.button('Reset', icon='refresh', on_click=reset_filter).props('dense flat size=sm')

        ui.separator()

        # Dashboard content container
        dashboard_container = ui.column().classes('w-full')
        with dashboard_container:
            build_dashboard(flight_stats)


@ui.page('/share/{share_id}')
def view_shared(share_id: str):
    """View a shared flight dashboard"""
    ui.colors(primary='#3b82f6')

    # Get share info to check for owner name
    from util.share import get_share_info
    share_info = get_share_info(share_id)
    owner_name = share_info.get('owner_name') if share_info else None

    with ui.header().classes('items-center justify-between'):
        ui.label('Sendy').classes('text-h4 font-bold')
        ui.button('Create Your Own', icon='home', on_click=lambda: ui.navigate.to('/')).props('flat text-color=white')

    with ui.column().classes('w-full p-4'):
        # Validate and load shared data
        if not validate_share_id(share_id):
            ui.label('Invalid or Expired Share Link').classes('text-h4 text-red')
            ui.label('This share link is either invalid or has expired.').classes('text-body1 mt-2')
            ui.button('Go to Home', on_click=lambda: ui.navigate.to('/')).classes('mt-4')
            return

        # Load the shared dataset
        shared_df, shared_stats = load_shared_dataset(share_id)

        if shared_df is None or not shared_stats:
            ui.label('Error Loading Shared Data').classes('text-h4 text-red')
            ui.label('Unable to load the shared flight data.').classes('text-body1 mt-2')
            ui.button('Go to Home', on_click=lambda: ui.navigate.to('/')).classes('mt-4')
            return

        # Display the dashboard with personalized title
        if owner_name:
            ui.label(f"{owner_name}'s Flights").classes('text-h3')
        else:
            ui.label('Shared Flights').classes('text-h3')

        # Show flight count and date range
        flight_count_text = f'Viewing {shared_stats.get("total_flights", 0)} flights'

        # Add date range if available
        if share_info and share_info.get('date_range'):
            date_range = share_info['date_range']
            start = date_range.get('start')
            end = date_range.get('end')
            if start or end:
                range_text = f" ({start or 'Beginning'} to {end or 'End'})"
                flight_count_text += range_text

        ui.label(flight_count_text).classes('text-body1 text-grey')
        ui.separator()

        build_dashboard(shared_stats)


# Load airports on startup
load_airports()


ui.run(title='Sendy', port=8080, favicon="static/favicon.png")
