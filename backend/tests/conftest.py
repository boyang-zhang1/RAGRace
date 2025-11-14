"""
Pytest configuration for DocAgent-Arena tests.

Loads environment variables from backend/.env file before running tests.
"""

from dotenv import load_dotenv
from pathlib import Path

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"  # backend/tests -> backend/.env
load_dotenv(dotenv_path=env_path)
