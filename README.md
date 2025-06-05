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

### Enhancements to Resource Tracking (Edit/Delete)

The Resource Tracking feature has been enhanced with capabilities to edit and delete existing entries:

- **Edit Entries**: On the "View All Usage Data" page, each resource entry now has an "Edit" button. Clicking this will take you to a form pre-filled with the entry's current data, where you can make modifications and save them.
- **Delete Entries**: Each entry on the "View All Usage Data" page also has a "Delete" button. Clicking this will prompt for confirmation, and if confirmed, will remove the entry from the database.

These actions can be found in the "Actions" column on the resource viewing page.


#### Filtering and Sorting Resource Data

The "View All Usage Data" page (`/view_resources`) now includes controls to filter and sort the displayed entries:

- **Filtering**:
    - **By Date Range**: You can specify a "Start Date" and/or "End Date" to narrow down entries within a specific period.
    - **By Resource Type**: A dropdown allows you to select a specific resource type (e.g., "Water", "Energy") or view "All Types".
- **Sorting**:
    - **Sort By**: You can choose to sort the data by "Date", "Resource Type", or "Quantity".
    - **Sort Order**: Data can be sorted in "Ascending" or "Descending" order. The default is by "Date" in "Descending" order.
- **Applying and Clearing**:
    - Click the "Apply" button to refresh the data view with your selected filters and sort order.
    - Click the "Clear" button to remove all active filters and reset the sorting to default.

A summary of any active filters and the current sort order is displayed above the data table for clarity.


#### Basic Visualizations

A new "View Usage Charts" page (`/charts`) has been added to provide basic visualizations of resource usage data.

- **Accessing Charts**: Links to this page are available on the homepage and the "View All Usage Data" page.
- **Current Chart**:
    - **Total Usage by Resource Type**: A bar chart displays the total quantity of each resource type used.
- **Filtering**:
    - The chart data can be filtered by a "Start Date" and "End Date". Use the provided date input fields and click "Apply Filters" to update the chart.
- **Technology**: Charts are rendered using Chart.js. Data is fetched dynamically from an API endpoint (`/api/resource_chart_data`).

This feature provides a quick visual overview of resource consumption patterns.

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
