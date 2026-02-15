"""
File handling utilities for JSON I/O operations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def save_json(data: Dict[str, Any], directory: Path, filename: str = None) -> Path:
    """
    Save dictionary to JSON file
    
    TODO: If filename is None, generate timestamp-based filename
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"schedule_{timestamp}.json"
    
    filepath = directory / filename
    directory.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file to dictionary"""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_latest_output(output_dir: Path) -> Path:
    """Get the most recently created output file"""
    files = list(output_dir.glob("*.json"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def get_latest_output_for_input(output_dir: Path, input_file: Path) -> Path:
    """Get the most recent output file that matches a specific input file."""
    base_name = Path(input_file).stem.replace("_input", "")
    pattern = f"{base_name}_output_*.json"
    files = list(output_dir.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)
