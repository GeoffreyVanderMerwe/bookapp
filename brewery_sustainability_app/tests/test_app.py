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

    # --- Tests for Filtering and Sorting ---

    def test_view_resources_no_filters_no_data(self):
        response = self.client.get('/view_resources')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tracked Resource Usage", response.data)
        self.assertIn(b"No resource usage data recorded yet.", response.data)
        self.assertIn(b"start_date", response.data)
        self.assertIn(b"resource_type", response.data)
        self.assertIn(b"sort_by", response.data)

    def _add_sample_data(self):
        with app.app_context():
            r1 = ResourceUsage(date=date(2023, 1, 10), resource_type="Water", quantity=100, unit="gallons")
            r2 = ResourceUsage(date=date(2023, 1, 15), resource_type="Energy", quantity=50, unit="kWh")
            r3 = ResourceUsage(date=date(2023, 1, 20), resource_type="Water", quantity=120, unit="gallons")
            r4 = ResourceUsage(date=date(2023, 2, 1), resource_type="Other", quantity=10, unit="units")
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()
            return r1, r2, r3, r4

    def _get_table_body_content(self, response_data_bytes):
        """Helper to extract content between <tbody> and </tbody>."""
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
        # Default sort is date descending. R4 (Feb 1) should be first.
        self.assertTrue(table_content.find("2023-02-01") < table_content.find("2023-01-20"), "Feb 1 should appear before Jan 20 in table")
        self.assertTrue(table_content.find("2023-01-20") < table_content.find("2023-01-15"), "Jan 20 should appear before Jan 15 in table")
        self.assertTrue(table_content.find("2023-01-15") < table_content.find("2023-01-10"), "Jan 15 should appear before Jan 10 in table")

    def test_view_resources_filter_by_resource_type(self):
        self._add_sample_data()
        response = self.client.get('/view_resources?resource_type=Water')
        self.assertEqual(response.status_code, 200)
        table_content = self._get_table_body_content(response.data)
        self.assertIn("Water", table_content)
        self.assertNotIn("Energy", table_content)
        self.assertNotIn("Other", table_content)
        self.assertIn("100", table_content) # r1 quantity
        self.assertIn("120", table_content) # r3 quantity
        # Check form repopulation (this is fine on full response data)
        self.assertIn(b'<option value="Water" selected', response.data)

    def test_view_resources_filter_by_date_range(self):
        self._add_sample_data()
        response = self.client.get('/view_resources?start_date=2023-01-12&end_date=2023-01-25')
        self.assertEqual(response.status_code, 200)
        table_content = self._get_table_body_content(response.data)
        self.assertNotIn("2023-01-10", table_content) # r1 excluded
        self.assertIn("2023-01-15", table_content)    # r2 included
        self.assertIn("2023-01-20", table_content)    # r3 included
        self.assertNotIn("2023-02-01", table_content) # r4 excluded
        # Check form repopulation
        self.assertIn(b'name="start_date" value="2023-01-12"', response.data)
        self.assertIn(b'name="end_date" value="2023-01-25"', response.data)

    def test_view_resources_filter_and_sort(self):
        self._add_sample_data()
        response = self.client.get('/view_resources?resource_type=Water&sort_by=quantity&sort_order=asc')
        self.assertEqual(response.status_code, 200)
        table_content = self._get_table_body_content(response.data)
        # For Water type, quantities are 100 and 120. Ascending means 100 then 120.
        self.assertTrue(table_content.find("100.0") < table_content.find("120.0"), "100 should appear before 120 in sorted table")
        self.assertNotIn("Energy", table_content)
        # Check form repopulation
        self.assertIn(b'<option value="Water" selected', response.data)
        self.assertIn(b'<option value="quantity" selected', response.data)
        self.assertIn(b'<option value="asc" selected', response.data)

    def test_view_resources_clear_filters(self):
        self._add_sample_data()
        response_filtered = self.client.get('/view_resources?resource_type=Energy')
        self.assertEqual(response_filtered.status_code, 200)
        table_content_filtered = self._get_table_body_content(response_filtered.data)
        self.assertNotIn("Water", table_content_filtered) # Ensure filter worked on table

        response_cleared = self.client.get('/view_resources') # Simulate clicking "Clear"
        self.assertEqual(response_cleared.status_code, 200)
        table_content_cleared = self._get_table_body_content(response_cleared.data)
        self.assertIn("Water", table_content_cleared)
        self.assertIn("Energy", table_content_cleared)
        self.assertIn("Other", table_content_cleared)
        # Check form repopulation (on full response data is fine for these)
        self.assertIn(b'<input type="date" id="start_date" name="start_date" value=""', response_cleared.data)
        self.assertIn(b'<option value="" selected', response_cleared.data) # "All Types"
        self.assertIn(b'<option value="date" selected', response_cleared.data) # Default sort_by
        self.assertIn(b'<option value="desc" selected', response_cleared.data) # Default sort_order

if __name__ == "__main__":
    unittest.main()
