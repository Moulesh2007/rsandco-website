import sys
import os

# Add your project directory to the path
project_home = '/home/Moulesh2007/rsandco-website'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['SECRET_KEY'] = 'rsandco-secret-key-2026'
os.environ['FLASK_ENV'] = 'production'

# Import the Flask app
from app import app as application
