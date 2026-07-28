import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables
os.environ.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'rsandco-secret-key-2026'))
os.environ.setdefault('FLASK_ENV', 'production')

# Import the Flask app
from app import app as application
