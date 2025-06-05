import unittest
import os
from app import app, db, ResourceUsage # App is in the current CWD for tests
from datetime import date

# Set the app to testing mode and configure a test database
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

class BasicTests(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Brewery Sustainability Platform", response.data)

    def test_add_resource_page_loads(self):
        response = self.client.get('/add_resource')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add New Resource Usage", response.data)

    # --- Tests for Filtering and Sorting (from previous step) ---

    def test_view_resources_no_filters_no_data(self):
        response = self.client.get('/view_resources')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tracked Resource Usage", response.data)
        self.assertIn(b"No resource usage data recorded yet.", response.data)
        self.assertIn(b"start_date", response.data)
        self.assertIn(b"resource_type", response.data)
        self.assertIn(b"sort_by", response.data)

    def _add_sample_data(self): # Renamed from _add_api_sample_data for general use if needed
        with app.app_context():
            r1 = ResourceUsage(date=date(2023, 1, 10), resource_type="Water", quantity=100, unit="gallons")
            r2 = ResourceUsage(date=date(2023, 1, 15), resource_type="Energy", quantity=50, unit="kWh")
            r3 = ResourceUsage(date=date(2023, 1, 20), resource_type="Water", quantity=120, unit="gallons")
            r4 = ResourceUsage(date=date(2023, 2, 1), resource_type="Other", quantity=10, unit="units")
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()
            return r1, r2, r3, r4

    def _get_table_body_content(self, response_data_bytes):
        response_data_str = response_data_bytes.decode('utf-8')
        table_body_start = response_data_str.find('<tbody>')
        table_body_end = response_data_str.find('</tbody>', table_body_start)
        if table_body_start != -1 and table_body_end != -1:
            return response_data_str[table_body_start + len('<tbody>'):table_body_end]
        return ""

    def test_view_resources_with_data_default_sort(self):
        self._add_sample_data()
        response = self.client.get('/view_resources')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"No resource usage data recorded yet.", response.data)
        table_content = self._get_table_body_content(response.data)
        self.assertTrue(table_content.find("2023-02-01") < table_content.find("2023-01-20"), "Feb 1 before Jan 20")
        self.assertTrue(table_content.find("2023-01-20") < table_content.find("2023-01-15"), "Jan 20 before Jan 15")
        self.assertTrue(table_content.find("2023-01-15") < table_content.find("2023-01-10"), "Jan 15 before Jan 10")

    def test_view_resources_filter_by_resource_type(self):
        self._add_sample_data()
        response = self.client.get('/view_resources?resource_type=Water')
        self.assertEqual(response.status_code, 200)
        table_content = self._get_table_body_content(response.data)
        self.assertIn("Water", table_content)
        self.assertNotIn("Energy", table_content)
        self.assertNotIn("Other", table_content)
        self.assertIn("100", table_content)
        self.assertIn("120", table_content)
        self.assertIn(b'<option value="Water" selected', response.data)

    def test_view_resources_filter_by_date_range(self):
        self._add_sample_data()
        response = self.client.get('/view_resources?start_date=2023-01-12&end_date=2023-01-25')
        self.assertEqual(response.status_code, 200)
        table_content = self._get_table_body_content(response.data)
        self.assertNotIn("2023-01-10", table_content)
        self.assertIn("2023-01-15", table_content)
        self.assertIn("2023-01-20", table_content)
        self.assertNotIn("2023-02-01", table_content)
        self.assertIn(b'name="start_date" value="2023-01-12"', response.data)
        self.assertIn(b'name="end_date" value="2023-01-25"', response.data)

    def test_view_resources_filter_and_sort(self):
        self._add_sample_data()
        response = self.client.get('/view_resources?resource_type=Water&sort_by=quantity&sort_order=asc')
        self.assertEqual(response.status_code, 200)
        table_content = self._get_table_body_content(response.data)
        self.assertTrue(table_content.find("100.0") < table_content.find("120.0"), "100 before 120")
        self.assertNotIn("Energy", table_content)
        self.assertIn(b'<option value="Water" selected', response.data)
        self.assertIn(b'<option value="quantity" selected', response.data)
        self.assertIn(b'<option value="asc" selected', response.data)

    def test_view_resources_clear_filters(self):
        self._add_sample_data()
        response_filtered = self.client.get('/view_resources?resource_type=Energy')
        self.assertEqual(response_filtered.status_code, 200)
        table_content_filtered = self._get_table_body_content(response_filtered.data)
        self.assertNotIn("Water", table_content_filtered)

        response_cleared = self.client.get('/view_resources')
        self.assertEqual(response_cleared.status_code, 200)
        table_content_cleared = self._get_table_body_content(response_cleared.data)
        self.assertIn("Water", table_content_cleared)
        self.assertIn("Energy", table_content_cleared)
        self.assertIn("Other", table_content_cleared)
        self.assertIn(b'<input type="date" id="start_date" name="start_date" value=""', response_cleared.data)
        self.assertIn(b'<option value="" selected', response_cleared.data)
        self.assertIn(b'<option value="date" selected', response_cleared.data)
        self.assertIn(b'<option value="desc" selected', response_cleared.data)

    # --- Tests for API Endpoint /api/resource_chart_data ---

    def test_api_resource_chart_data_empty_db(self):
        """Test /api/resource_chart_data with no data in the database."""
        response = self.client.get('/api/resource_chart_data')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], [])
        self.assertEqual(len(json_data['datasets']), 1)
        self.assertEqual(json_data['datasets'][0]['data'], [])
        self.assertEqual(json_data['datasets'][0]['label'], 'Total Quantity Used')

    def _add_api_sample_data(self): # Kept separate if API needs different/more specific data later
        """Helper to add data specifically for API chart tests."""
        with app.app_context():
            r1 = ResourceUsage(date=date(2023, 3, 10), resource_type="Water", quantity=100, unit="gallons")
            r2 = ResourceUsage(date=date(2023, 3, 15), resource_type="Energy", quantity=50, unit="kWh")
            r3 = ResourceUsage(date=date(2023, 3, 20), resource_type="Water", quantity=120, unit="gallons")
            r4 = ResourceUsage(date=date(2023, 4, 1), resource_type="Other", quantity=10, unit="units")
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()

    def test_api_resource_chart_data_with_data_no_filters(self):
        """Test /api/resource_chart_data with data and no filters."""
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()

        self.assertEqual(json_data['labels'], ['Energy', 'Other', 'Water'])
        self.assertEqual(len(json_data['datasets']), 1)
        self.assertEqual(json_data['datasets'][0]['label'], 'Total Quantity Used')
        self.assertEqual(json_data['datasets'][0]['data'], [50.0, 10.0, 220.0])

    def test_api_resource_chart_data_with_date_filters(self):
        """Test /api/resource_chart_data with start_date and end_date filters."""
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?start_date=2023-03-12&end_date=2023-03-25')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Energy', 'Water'])
        self.assertEqual(len(json_data['datasets']), 1)
        self.assertEqual(json_data['datasets'][0]['data'], [50.0, 120.0])

    def test_api_resource_chart_data_with_start_date_only(self):
        """Test /api/resource_chart_data with only start_date filter."""
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?start_date=2023-03-16')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Other', 'Water'])
        self.assertEqual(json_data['datasets'][0]['data'], [10.0, 120.0])

    def test_api_resource_chart_data_with_end_date_only(self):
        """Test /api/resource_chart_data with only end_date filter."""
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?end_date=2023-03-18')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Energy', 'Water'])
        self.assertEqual(json_data['datasets'][0]['data'], [50.0, 100.0])

    def test_api_resource_chart_data_invalid_date_format(self):
        """Test API with invalid date format (should be ignored, returning all data)."""
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?start_date=invalid-date')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(len(json_data['labels']), 3) # All 3 resource types (Energy, Other, Water)

if __name__ == "__main__":
    unittest.main()
