#!/bin/bash

# Set up the environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Initialize the database and create the default admin user
python init_db.py

# Run the Flask application
flask run --host=0.0.0.0 --port=5000
