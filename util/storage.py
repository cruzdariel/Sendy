# save/load per-user datasets (files/db)
import os
import json
import pickle
from pathlib import Path
import pandas as pd


# Storage directory for user datasets
STORAGE_DIR = Path('data/user_datasets')
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_dataset(dataset_id: str, flights_df: pd.DataFrame, stats: dict) -> bool:
    """
    Save a flight dataset and its computed statistics to disk.

    Args:
        dataset_id: Unique identifier for this dataset
        flights_df: DataFrame containing flight data
        stats: Dictionary of computed statistics

    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        dataset_path = STORAGE_DIR / dataset_id
        dataset_path.mkdir(exist_ok=True)

        # Save the DataFrame as CSV
        flights_df.to_csv(dataset_path / 'flights.csv', index=False)

        # Save stats (without the DataFrame inside it)
        stats_copy = stats.copy()
        if 'flights_data' in stats_copy:
            del stats_copy['flights_data']  # Don't duplicate the DataFrame

        with open(dataset_path / 'stats.json', 'w') as f:
            json.dump(stats_copy, f, indent=2, default=str)

        # Save metadata
        metadata = {
            'dataset_id': dataset_id,
            'total_flights': len(flights_df),
            'created_at': pd.Timestamp.now().isoformat()
        }
        with open(dataset_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Dataset {dataset_id} saved successfully")
        return True
    except Exception as e:
        print(f"Error saving dataset {dataset_id}: {e}")
        return False


def load_dataset(dataset_id: str) -> tuple:
    """
    Load a previously saved flight dataset and its statistics.

    Args:
        dataset_id: Unique identifier for the dataset to load

    Returns:
        tuple: (flights_df, stats) or (None, None) if not found
    """
    try:
        dataset_path = STORAGE_DIR / dataset_id

        if not dataset_path.exists():
            print(f"Dataset {dataset_id} not found")
            return None, None

        # Load the DataFrame
        flights_df = pd.read_csv(dataset_path / 'flights.csv')

        # Load stats
        with open(dataset_path / 'stats.json', 'r') as f:
            stats = json.load(f)

        # Add the DataFrame back to stats
        stats['flights_data'] = flights_df

        print(f"Dataset {dataset_id} loaded successfully")
        return flights_df, stats
    except Exception as e:
        print(f"Error loading dataset {dataset_id}: {e}")
        return None, None


def list_datasets() -> list:
    """
    List all saved datasets.

    Returns:
        list: List of dictionaries containing dataset metadata
    """
    datasets = []
    try:
        for dataset_dir in STORAGE_DIR.iterdir():
            if dataset_dir.is_dir():
                metadata_file = dataset_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        datasets.append(metadata)
    except Exception as e:
        print(f"Error listing datasets: {e}")

    return datasets


def delete_dataset(dataset_id: str) -> bool:
    """
    Delete a saved dataset.

    Args:
        dataset_id: Unique identifier for the dataset to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        dataset_path = STORAGE_DIR / dataset_id

        if not dataset_path.exists():
            print(f"Dataset {dataset_id} not found")
            return False

        # Delete all files in the dataset directory
        for file in dataset_path.iterdir():
            file.unlink()

        # Delete the directory itself
        dataset_path.rmdir()

        print(f"Dataset {dataset_id} deleted successfully")
        return True
    except Exception as e:
        print(f"Error deleting dataset {dataset_id}: {e}")
        return False


def dataset_exists(dataset_id: str) -> bool:
    """
    Check if a dataset exists.

    Args:
        dataset_id: Unique identifier for the dataset

    Returns:
        bool: True if dataset exists, False otherwise
    """
    dataset_path = STORAGE_DIR / dataset_id
    return dataset_path.exists() and (dataset_path / 'metadata.json').exists()
