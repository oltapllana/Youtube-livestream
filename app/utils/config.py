"""
Configuration file for TV Scheduling Backend
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
ALGORITHM_DIR = BASE_DIR / "app" / "algorithm" / "AA_25-26"
DATA_INPUT_DIR = ALGORITHM_DIR / "data" / "input"
DATA_OUTPUT_DIR = ALGORITHM_DIR / "data" / "output"

# Create directories if they don't exist
DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
API_TITLE = "TV Scheduling API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "API for TV Schedule Optimization using Beam Search Algorithm"

# Algorithm Configuration
ALGORITHM_SCRIPT = ALGORITHM_DIR / "main.py"
MAX_EXECUTION_TIME = 300  # seconds

# Default scheduling parameters
DEFAULT_OPENING_TIME = 480  # 8:00 AM (minutes from midnight)
DEFAULT_CLOSING_TIME = 1380  # 11:00 PM
DEFAULT_MIN_DURATION = 30  # minutes
DEFAULT_CHANNELS_COUNT = 10
DEFAULT_SWITCH_PENALTY = 10
DEFAULT_TERMINATION_PENALTY = 20
DEFAULT_MAX_CONSECUTIVE_GENRE = 2

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
