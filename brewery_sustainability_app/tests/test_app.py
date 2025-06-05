import unittest
import os
from app import app, db, ResourceUsage, WasteEntry
from datetime import date

app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['WTF_CSRF_ENABLED'] = False

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

    # --- Tests for Filtering and Sorting (Resource Usage) ---
    def test_view_resources_no_filters_no_data(self):
        response = self.client.get('/view_resources')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tracked Resource Usage", response.data)
        self.assertIn(b"No resource usage data recorded yet.", response.data)

    def _add_sample_resource_data(self):
        with app.app_context():
            r1 = ResourceUsage(date=date(2023, 1, 10), resource_type="Water", quantity=100, unit="gallons")
            r2 = ResourceUsage(date=date(2023, 1, 15), resource_type="Energy", quantity=50, unit="kWh")
            r3 = ResourceUsage(date=date(2023, 1, 20), resource_type="Water", quantity=120, unit="gallons")
            r4 = ResourceUsage(date=date(2023, 2, 1), resource_type="Other", quantity=10, unit="units")
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()
            # Returning IDs might be safer if objects become detached, but for these tests, objects worked.
            return r1, r2, r3, r4

    def _get_table_body_content(self, response_data_bytes):
        response_data_str = response_data_bytes.decode('utf-8')
        table_body_start = response_data_str.find('<tbody>')
        table_body_end = response_data_str.find('</tbody>', table_body_start)
        if table_body_start != -1 and table_body_end != -1:
            return response_data_str[table_body_start + len('<tbody>'):table_body_end]
        return ""

    def test_view_resources_with_data_default_sort(self):
        self._add_sample_resource_data()
        response = self.client.get('/view_resources')
        table_content = self._get_table_body_content(response.data)
        self.assertTrue(table_content.find("2023-02-01") < table_content.find("2023-01-20"))

    def test_view_resources_filter_by_resource_type(self):
        self._add_sample_resource_data()
        response = self.client.get('/view_resources?resource_type=Water')
        table_content = self._get_table_body_content(response.data)
        self.assertIn("Water", table_content)
        self.assertNotIn("Energy", table_content)

    def test_view_resources_filter_by_date_range(self):
        self._add_sample_resource_data()
        response = self.client.get('/view_resources?start_date=2023-01-12&end_date=2023-01-25')
        table_content = self._get_table_body_content(response.data)
        self.assertNotIn("2023-01-10", table_content)
        self.assertIn("2023-01-15", table_content)

    def test_view_resources_filter_and_sort(self):
        self._add_sample_resource_data()
        response = self.client.get('/view_resources?resource_type=Water&sort_by=quantity&sort_order=asc')
        table_content = self._get_table_body_content(response.data)
        self.assertTrue(table_content.find("100.0") < table_content.find("120.0"))

    def test_view_resources_clear_filters(self):
        self._add_sample_resource_data()
        response_filtered = self.client.get('/view_resources?resource_type=Energy')
        table_content_filtered = self._get_table_body_content(response_filtered.data)
        self.assertNotIn("Water", table_content_filtered)
        response_cleared = self.client.get('/view_resources')
        table_content_cleared = self._get_table_body_content(response_cleared.data)
        self.assertIn("Water", table_content_cleared)

    # --- Tests for API Endpoint /api/resource_chart_data ---
    def test_api_resource_chart_data_empty_db(self):
        response = self.client.get('/api/resource_chart_data')
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], [])

    def _add_api_sample_data(self):
        with app.app_context():
            ResourceUsage.query.delete()
            WasteEntry.query.delete()
            db.session.commit()
            r1 = ResourceUsage(date=date(2023, 3, 10), resource_type="Water", quantity=100, unit="gallons")
            r2 = ResourceUsage(date=date(2023, 3, 15), resource_type="Energy", quantity=50, unit="kWh")
            r3 = ResourceUsage(date=date(2023, 3, 20), resource_type="Water", quantity=120, unit="gallons")
            r4 = ResourceUsage(date=date(2023, 4, 1), resource_type="Other", quantity=10, unit="units")
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()

    def test_api_resource_chart_data_with_data_no_filters(self):
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data')
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Energy', 'Other', 'Water'])
        self.assertEqual(json_data['datasets'][0]['data'], [50.0, 10.0, 220.0])

    def test_api_resource_chart_data_with_date_filters(self):
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?start_date=2023-03-12&end_date=2023-03-25')
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Energy', 'Water'])
        self.assertEqual(json_data['datasets'][0]['data'], [50.0, 120.0])

    def test_api_resource_chart_data_with_start_date_only(self):
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?start_date=2023-03-16')
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Other', 'Water'])
        self.assertEqual(json_data['datasets'][0]['data'], [10.0, 120.0])

    def test_api_resource_chart_data_with_end_date_only(self):
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?end_date=2023-03-18')
        json_data = response.get_json()
        self.assertEqual(json_data['labels'], ['Energy', 'Water'])
        self.assertEqual(json_data['datasets'][0]['data'], [50.0, 100.0])

    def test_api_resource_chart_data_invalid_date_format(self):
        self._add_api_sample_data()
        response = self.client.get('/api/resource_chart_data?start_date=invalid-date')
        json_data = response.get_json()
        self.assertEqual(len(json_data['labels']), 3)

    # --- Tests for Waste Management (Add/View) ---
    def test_add_waste_get_page(self):
        response = self.client.get('/add_waste')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add New Waste Entry", response.data)

    def test_add_waste_post_success(self):
        with self.client:
            response = self.client.post('/add_waste', data={
                'date': '2023-04-01', 'waste_type': 'Spent Grain', 'quantity': '250.75',
                'unit': 'kg', 'disposal_method': 'Repurposed (e.g., animal feed)', 'notes': 'Sent to local farm'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Waste entry added successfully!", response.data)
            self.assertIn(b"Spent Grain", response.data)

    def test_add_waste_post_invalid_data_missing_type(self):
        with self.client:
            response = self.client.post('/add_waste', data={'date': '2023-04-02', 'quantity': '10', 'unit': 'bins', 'disposal_method':'Recycled'}, follow_redirects=True)
            self.assertEqual(response.status_code, 400)
            self.assertIn(b"Waste Type is required.", response.data)

    def test_add_waste_post_invalid_quantity_negative(self):
        with self.client:
            response = self.client.post('/add_waste', data={
                'date': '2023-04-03', 'waste_type': 'Glass', 'quantity': '-5', 'unit': 'kg', 'disposal_method': 'Recycled'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 400)
            self.assertIn(b"Quantity must be a positive number.", response.data)

    def test_view_waste_no_entries(self):
        response = self.client.get('/view_waste')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No waste entries recorded yet.", response.data)

    def test_view_waste_with_entries(self):
        with app.app_context():
            entry1 = WasteEntry(date=date(2023, 4, 5), waste_type="Cardboard", quantity=30, unit="kg", disposal_method="Recycled", notes="Clean cardboard")
            db.session.add(entry1)
            db.session.commit()
        response = self.client.get('/view_waste')
        table_content = self._get_table_body_content(response.data)
        self.assertIn("Cardboard", table_content)
        self.assertIn("Clean cardboard", table_content)

    # --- Tests for Edit/Delete Waste Management ---

    def _add_single_waste_entry_for_edit_delete(self, notes_content="Initial notes"):
        with app.app_context():
            WasteEntry.query.filter_by(date=date(2023, 5, 1), notes=notes_content).delete() # More specific delete
            db.session.commit()

            entry = WasteEntry(
                date=date(2023, 5, 1),
                waste_type="Glass",
                quantity=25.5,
                unit="kg",
                disposal_method="Recycled",
                notes=notes_content
            )
            db.session.add(entry)
            db.session.commit()
            entry_id = entry.id
            # db.session.expunge(entry) # Not strictly necessary if only returning ID
            return entry_id

    def test_edit_waste_get_page_existing_entry(self):
        entry_id = self._add_single_waste_entry_for_edit_delete()
        response = self.client.get(f'/edit_waste/{entry_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Edit Waste Entry", response.data)
        self.assertIn(b"Glass", response.data)
        self.assertIn(b"25.5", response.data)
        self.assertIn(b"Initial notes", response.data)

    def test_edit_waste_get_page_non_existent_entry(self):
        response = self.client.get('/edit_waste/9999')
        self.assertEqual(response.status_code, 404)

    def test_edit_waste_post_success(self):
        entry_id = self._add_single_waste_entry_for_edit_delete()
        with self.client:
            response = self.client.post(f'/edit_waste/{entry_id}', data={
                'date': '2023-05-02', 'waste_type': 'Cardboard', 'quantity': '30.0',
                'unit': 'kg', 'disposal_method': 'Recycled', 'notes': 'Updated notes'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Waste entry updated successfully!", response.data)
            table_content = self._get_table_body_content(response.data)
            self.assertIn("Cardboard", table_content)
            self.assertIn("Updated notes", table_content)

            with app.app_context(): # Re-fetch within context
                updated_entry = WasteEntry.query.get(entry_id)
                self.assertEqual(updated_entry.date, date(2023, 5, 2))
                self.assertEqual(updated_entry.waste_type, 'Cardboard')
                self.assertEqual(updated_entry.notes, 'Updated notes')

    def test_edit_waste_post_invalid_data(self):
        entry_id = self._add_single_waste_entry_for_edit_delete()
        with self.client:
            response = self.client.post(f'/edit_waste/{entry_id}', data={
                'date': '2023-05-01', 'waste_type': 'Glass', 'quantity': '',
                'unit': 'kg', 'disposal_method': 'Recycled'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 400)
            self.assertIn(b"Edit Waste Entry", response.data)
            self.assertIn(b"Quantity is required.", response.data)
            with app.app_context(): # Re-fetch within context
                original_entry = WasteEntry.query.get(entry_id)
                self.assertEqual(original_entry.quantity, 25.5)

    def test_delete_waste_post_success(self):
        entry_id = self._add_single_waste_entry_for_edit_delete(notes_content="Notes to be deleted")
        with self.client:
            response = self.client.post(f'/delete_waste/{entry_id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Waste entry deleted successfully!", response.data)
            table_content = self._get_table_body_content(response.data)
            self.assertNotIn("Notes to be deleted", table_content)
            with app.app_context(): # Check within context
                deleted_entry = WasteEntry.query.get(entry_id)
                self.assertIsNone(deleted_entry)

    def test_delete_waste_post_non_existent_entry(self):
        response = self.client.post('/delete_waste/9999', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
