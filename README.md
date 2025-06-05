# SAAS Platform for Craft Brewery Sustainability

This project is the beginning of a SAAS platform designed to help craft breweries manage and improve their sustainability practices.

## Project Structure

The project currently has the following basic structure:

```
├── brewery_sustainability_app/
│   ├── app.py                   # Main Flask application file
│   ├── requirements.txt         # Python package dependencies
│   ├── static/                  # For static assets (CSS, JavaScript, images)
│   └── templates/               # For HTML templates
│       └── index.html           # Basic landing page
└── README.md                    # This file
```

## Getting Started

To run the application locally, follow these steps:

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Navigate to the application directory:**
    ```bash
    cd brewery_sustainability_app
    ```

3.  **Create and activate a virtual environment:**
    On macOS and Linux:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    On Windows:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

4.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Flask development server:**
    ```bash
    python app.py
    ```

    The application will be accessible at `http://127.0.0.1:5000/` in your web browser.

## Next Steps

This is just the initial scaffolding. Future development will focus on implementing the core features outlined in the project proposal, such as:
- Resource Tracking
- Waste Management
- Carbon Footprint Calculation

Stay tuned!
## Features Implemented

### Resource Tracking

This application now includes a basic resource tracking feature that allows users to:
- **Add Resource Usage Data**: Navigate to the "Add Resource Usage" page (linked from the homepage) to input daily or periodic usage for resources like water, energy, raw materials, etc. The form includes fields for date, resource type, quantity, and unit.
- **View Tracked Data**: Navigate to the "View All Usage Data" page (linked from the homepage) to see a table of all submitted resource usage data, ordered by the most recent entries first.

## Database Setup

This application uses an SQLite database to store resource usage data. The database file (`sustainability.db`) is located in the `brewery_sustainability_app/instance/` directory.

To initialize the database and create the necessary tables for the first time, ensure you are in the `brewery_sustainability_app` directory and run the following command:

```bash
flask init-db
```
This command should be run after installing dependencies and before running the application for the first time.

## Updated Project Structure

The project structure has evolved to include the application logic and database:

```
.
├── brewery_sustainability_app/
│   ├── app.py                   # Main Flask application file
│   ├── requirements.txt         # Python package dependencies
│   ├── instance/                # Instance folder (created automatically)
│   │   └── sustainability.db    # SQLite database file (after running flask init-db)
│   ├── static/                  # For static assets (CSS, JavaScript, images)
│   ├── templates/               # For HTML templates
│   │   ├── index.html           # Main landing page
│   │   ├── add_resource.html    # Form to add resource usage
│   │   └── view_resources.html  # Page to display tracked resources
│   └── tests/                   # Directory for unit tests
│       ├── __init__.py          # Makes 'tests' a Python package
│       └── test_app.py          # Basic test structure (implementation pending)
└── README.md                    # This file
```
