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