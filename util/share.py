# create/validate share IDs, URLs
import secrets
import string
import json
from pathlib import Path
from datetime import datetime, timedelta
from util.storage import save_dataset, load_dataset, dataset_exists


# Storage directory for share mappings
SHARE_DIR = Path('data/shares')
SHARE_DIR.mkdir(parents=True, exist_ok=True)


def generate_share_id(length: int = 8) -> str:
    """
    Generate a random share ID.

    Args:
        length: Length of the share ID (default: 8)

    Returns:
        str: Random alphanumeric share ID
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_share(flights_df, stats, expiry_days: int = 30, owner_name: str = None, date_range: dict = None) -> str:
    """
    Create a shareable link for a flight dataset.

    Args:
        flights_df: DataFrame containing flight data
        stats: Dictionary of computed statistics
        expiry_days: Number of days until the share expires (default: 30)
        owner_name: Name of the person sharing (optional)
        date_range: Dictionary with 'start' and 'end' date strings (optional)

    Returns:
        str: Share ID that can be used to access the dataset
    """
    # Generate unique share ID
    share_id = generate_share_id()
    while share_exists(share_id):
        share_id = generate_share_id()

    # Save the dataset using the share ID
    if not save_dataset(share_id, flights_df, stats):
        return None

    # Create share metadata
    expiry_date = datetime.now() + timedelta(days=expiry_days)
    share_metadata = {
        'share_id': share_id,
        'created_at': datetime.now().isoformat(),
        'expires_at': expiry_date.isoformat(),
        'total_flights': len(flights_df),
        'is_active': True,
        'owner_name': owner_name if owner_name else None,
        'date_range': date_range if date_range else None
    }

    # Save share metadata
    share_file = SHARE_DIR / f'{share_id}.json'
    with open(share_file, 'w') as f:
        json.dump(share_metadata, f, indent=2)

    print(f"Share created: {share_id}")
    return share_id


def validate_share_id(share_id: str) -> bool:
    """
    Validate if a share ID is valid and not expired.

    Args:
        share_id: Share ID to validate

    Returns:
        bool: True if valid and not expired, False otherwise
    """
    if not share_exists(share_id):
        return False

    try:
        share_file = SHARE_DIR / f'{share_id}.json'
        with open(share_file, 'r') as f:
            metadata = json.load(f)

        # Check if share is active
        if not metadata.get('is_active', True):
            return False

        # Check expiry
        expires_at = datetime.fromisoformat(metadata['expires_at'])
        if datetime.now() > expires_at:
            print(f"Share {share_id} has expired")
            return False

        return True
    except Exception as e:
        print(f"Error validating share {share_id}: {e}")
        return False


def load_shared_dataset(share_id: str) -> tuple:
    """
    Load a dataset using a share ID.

    Args:
        share_id: Share ID to load

    Returns:
        tuple: (flights_df, stats) or (None, None) if invalid/expired
    """
    if not validate_share_id(share_id):
        print(f"Invalid or expired share ID: {share_id}")
        return None, None

    return load_dataset(share_id)


def get_share_url(share_id: str, base_url: str = 'https://sendy.dariel.us') -> str:
    """
    Generate a shareable URL for a share ID.

    Args:
        share_id: Share ID
        base_url: Base URL of the application (default: localhost)

    Returns:
        str: Full shareable URL
    """
    return f"{base_url}/share/{share_id}"


def share_exists(share_id: str) -> bool:
    """
    Check if a share ID exists.

    Args:
        share_id: Share ID to check

    Returns:
        bool: True if share exists, False otherwise
    """
    share_file = SHARE_DIR / f'{share_id}.json'
    return share_file.exists() and dataset_exists(share_id)


def deactivate_share(share_id: str) -> bool:
    """
    Deactivate a share (without deleting the data).

    Args:
        share_id: Share ID to deactivate

    Returns:
        bool: True if successful, False otherwise
    """
    if not share_exists(share_id):
        print(f"Share {share_id} not found")
        return False

    try:
        share_file = SHARE_DIR / f'{share_id}.json'
        with open(share_file, 'r') as f:
            metadata = json.load(f)

        metadata['is_active'] = False
        metadata['deactivated_at'] = datetime.now().isoformat()

        with open(share_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Share {share_id} deactivated")
        return True
    except Exception as e:
        print(f"Error deactivating share {share_id}: {e}")
        return False


def get_share_info(share_id: str) -> dict:
    """
    Get information about a share.

    Args:
        share_id: Share ID

    Returns:
        dict: Share metadata or None if not found
    """
    if not share_exists(share_id):
        return None

    try:
        share_file = SHARE_DIR / f'{share_id}.json'
        with open(share_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error getting share info for {share_id}: {e}")
        return None


def list_active_shares() -> list:
    """
    List all active (non-expired) shares.

    Returns:
        list: List of active share metadata dictionaries
    """
    active_shares = []
    try:
        for share_file in SHARE_DIR.glob('*.json'):
            with open(share_file, 'r') as f:
                metadata = json.load(f)

            share_id = metadata['share_id']
            if validate_share_id(share_id):
                active_shares.append(metadata)
    except Exception as e:
        print(f"Error listing active shares: {e}")

    return active_shares
