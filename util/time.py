# time formatting, durations
from airportsdata import load
import pytz

def local_to_utc(local_time, airport_code):
    """
    Convert a naive local datetime to UTC based on the airport code.

    Args:
        local_time (datetime): Naive local datetime.
        airport_code (str): ICAO or IATA code of the airport.

    Returns:
        datetime: UTC datetime (naive, without tzinfo).
    """

    airports = load('IATA')  # defaults to IATA codes, switches to ICAO if needed
    code = airport_code.upper()

    # Try IATA, then ICAO if not found
    tzname = None
    info = airports.get(code)
    if info and 'timezone' in info and info['timezone']:
        tzname = info['timezone']
    else:
        airports_icao = load('ICAO')
        info = airports_icao.get(code)
        if info and 'timezone' in info and info['timezone']:
            tzname = info['timezone']

    if not tzname:
        raise ValueError(f"Timezone not found for airport code '{airport_code}'")

    tz = pytz.timezone(tzname)
    # Localize and convert to UTC
    local_dt = tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    # Return as naive UTC for compatibility with most code
    return utc_dt.replace(tzinfo=None)