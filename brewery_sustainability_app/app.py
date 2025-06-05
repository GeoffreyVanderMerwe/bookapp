from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import datetime
import os

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')

# --- Database Configuration ---
instance_folder_path = app.instance_path
if not os.path.exists(instance_folder_path):
    os.makedirs(instance_folder_path)
    print(f"Created instance folder at: {instance_folder_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_folder_path, 'sustainability.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

db = SQLAlchemy(app)

# --- Models ---
class ResourceUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    resource_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<ResourceUsage ID: {self.id} on {self.date} - {self.resource_type}: {self.quantity} {self.unit}>'

# --- New Model: WasteEntry ---
class WasteEntry(db.Model):
    __tablename__ = 'waste_entries' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    waste_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    disposal_method = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True) # db.Text should be available via SQLAlchemy instance

    def __repr__(self):
        return f'<WasteEntry {self.id} on {self.date}: {self.waste_type} - {self.quantity} {self.unit}>'

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_resource', methods=['GET', 'POST'])
def add_resource():
    form_data_to_render = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        date_str = request.form.get('date')
        resource_type = request.form.get('resource_type')
        quantity_str = request.form.get('quantity')
        unit = request.form.get('unit')

        if not date_str:
            flash('Date is required.', 'error')
            return render_template('add_resource.html', form_data=form_data_to_render), 400
        try:
            entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return render_template('add_resource.html', form_data=form_data_to_render), 400

        if not resource_type:
            flash('Resource type is required.', 'error')
            return render_template('add_resource.html', form_data=form_data_to_render), 400

        if not quantity_str:
            flash('Quantity is required.', 'error')
            return render_template('add_resource.html', form_data=form_data_to_render), 400
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                flash('Quantity must be a positive number.', 'error')
                return render_template('add_resource.html', form_data=form_data_to_render), 400
        except ValueError:
            flash('Quantity must be a valid number.', 'error')
            return render_template('add_resource.html', form_data=form_data_to_render), 400

        if not unit or len(unit.strip()) == 0:
            flash('Unit is required and cannot be empty.', 'error')
            return render_template('add_resource.html', form_data=form_data_to_render), 400

        try:
            new_usage = ResourceUsage(date=entry_date,
                                      resource_type=resource_type,
                                      quantity=quantity,
                                      unit=unit.strip())
            db.session.add(new_usage)
            db.session.commit()
            flash('Resource usage added successfully!', 'success')
            return redirect(url_for('view_resources'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error when adding resource: {e}")
            flash('An error occurred while saving the data to the database.', 'error') # User-friendly message
            return render_template('add_resource.html', form_data=form_data_to_render), 500

    return render_template('add_resource.html', form_data={}) # Corrected from previous form_data=form_data_to_render

@app.route('/view_resources')
def view_resources():
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        resource_type_filter = request.args.get('resource_type')
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')

        query = ResourceUsage.query

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(ResourceUsage.date >= start_date)
            except ValueError:
                flash('Invalid start date format. Please use YYYY-MM-DD.', 'error')

        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(ResourceUsage.date <= end_date)
            except ValueError:
                flash('Invalid end date format. Please use YYYY-MM-DD.', 'error')

        if resource_type_filter and resource_type_filter != "":
            query = query.filter(ResourceUsage.resource_type == resource_type_filter)

        sort_column = ResourceUsage.date
        if sort_by == 'resource_type':
            sort_column = ResourceUsage.resource_type
        elif sort_by == 'quantity':
            sort_column = ResourceUsage.quantity

        if sort_order == 'asc':
            query = query.order_by(sort_column.asc(), ResourceUsage.id.asc())
        else:
            query = query.order_by(sort_column.desc(), ResourceUsage.id.desc())

        all_resources = query.all()

    except Exception as e:
        app.logger.error(f"Error fetching or filtering resources: {e}")
        flash('Could not retrieve or filter resource data from the database.', 'error')
        all_resources = []

    return render_template('view_resources.html',
                           resources=all_resources
                          )

@app.route('/edit_resource/<int:id>', methods=['GET', 'POST'])
def edit_resource(id):
    resource_to_edit = ResourceUsage.query.get_or_404(id)

    if request.method == 'POST':
        form_data_for_template = request.form
        date_str = request.form.get('date')
        resource_type = request.form.get('resource_type')
        quantity_str = request.form.get('quantity')
        unit = request.form.get('unit')

        error_occurred = False
        entry_date = None
        quantity = None

        if not date_str:
            flash('Date is required.', 'error')
            error_occurred = True
        else:
            try:
                entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
                error_occurred = True

        if not resource_type:
            flash('Resource type is required.', 'error')
            error_occurred = True

        if not quantity_str:
            flash('Quantity is required.', 'error')
            error_occurred = True
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    flash('Quantity must be a positive number.', 'error')
                    error_occurred = True
            except ValueError:
                flash('Quantity must be a valid number.', 'error')
                error_occurred = True

        if not unit or len(unit.strip()) == 0:
            flash('Unit is required and cannot be empty.', 'error')
            error_occurred = True

        if error_occurred:
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400

        try:
            resource_to_edit.date = entry_date
            resource_to_edit.resource_type = resource_type
            resource_to_edit.quantity = quantity
            resource_to_edit.unit = unit.strip()

            db.session.commit()
            flash('Resource usage updated successfully!', 'success')
            return redirect(url_for('view_resources'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error when updating resource ID {id}: {e}")
            flash('An error occurred while updating the data. Please try again.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 500

    return render_template('edit_resource.html', resource=resource_to_edit, form_data=None)

@app.route('/delete_resource/<int:id>', methods=['POST'])
def delete_resource(id):
    resource_to_delete = ResourceUsage.query.get_or_404(id)
    try:
        db.session.delete(resource_to_delete)
        db.session.commit()
        flash('Resource usage entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting resource ID {id}: {e}")
        flash('An error occurred while deleting the entry. Please try again.', 'error')
    return redirect(url_for('view_resources'))

@app.route('/view_waste')
def view_waste():
    try:
        all_waste_entries = WasteEntry.query.order_by(WasteEntry.date.desc(), WasteEntry.id.desc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching waste entries: {e}")
        flash('Could not retrieve waste data from the database.', 'error')
        all_waste_entries = []
    return render_template('view_waste.html', waste_entries=all_waste_entries)

@app.route('/add_waste', methods=['GET', 'POST'])
def add_waste():
    if request.method == 'POST':
        form_data_for_template = request.form
        date_str = request.form.get('date')
        waste_type = request.form.get('waste_type')
        quantity_str = request.form.get('quantity')
        unit = request.form.get('unit')
        disposal_method = request.form.get('disposal_method')
        notes = request.form.get('notes', '').strip() # Ensure notes is stripped, default to empty

        error_occurred = False
        entry_date = None
        quantity = None

        if not date_str:
            flash('Date is required.', 'error')
            error_occurred = True
        else:
            try:
                entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
                error_occurred = True

        if not waste_type: # Check if waste_type is empty
            flash('Waste Type is required.', 'error') # Corrected flash message
            error_occurred = True

        if not quantity_str:
            flash('Quantity is required.', 'error')
            error_occurred = True
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    flash('Quantity must be a positive number.', 'error')
                    error_occurred = True
            except ValueError:
                flash('Quantity must be a valid number.', 'error')
                error_occurred = True

        if not unit or len(unit.strip()) == 0:
            flash('Unit is required.', 'error') # Corrected flash message
            error_occurred = True

        if not disposal_method: # Check if disposal_method is empty
            flash('Disposal method is required.','error')
            error_occurred = True

        if error_occurred:
            return render_template('add_waste.html', form_data=form_data_for_template), 400

        try:
            new_waste_entry = WasteEntry(
                date=entry_date,
                waste_type=waste_type.strip(),
                quantity=quantity,
                unit=unit.strip(),
                disposal_method=disposal_method.strip(), # Ensure disposal_method is stripped
                notes=notes if notes else None
            )
            db.session.add(new_waste_entry)
            db.session.commit()
            flash('Waste entry added successfully!', 'success')
            return redirect(url_for('view_waste'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error when adding waste entry: {e}")
            flash('An error occurred while saving the waste entry. Please try again.', 'error')
            return render_template('add_waste.html', form_data=form_data_for_template), 500

    return render_template('add_waste.html', form_data={})

@app.route('/edit_waste/<int:id>', methods=['GET', 'POST'])
def edit_waste(id):
    waste_entry_to_edit = WasteEntry.query.get_or_404(id)

    if request.method == 'POST':
        form_data_for_template = request.form
        date_str = request.form.get('date')
        waste_type = request.form.get('waste_type')
        quantity_str = request.form.get('quantity')
        unit = request.form.get('unit')
        disposal_method = request.form.get('disposal_method')
        notes = request.form.get('notes', '').strip()

        error_occurred = False
        entry_date = None
        quantity = None

        if not date_str:
            flash('Date is required.', 'error')
            error_occurred = True
        else:
            try:
                entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
                error_occurred = True

        if not waste_type: # Check if waste_type is empty
            flash('Waste type is required.', 'error') # Corrected to match case in test
            error_occurred = True

        if not quantity_str:
            flash('Quantity is required.', 'error')
            error_occurred = True
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    flash('Quantity must be a positive number.', 'error')
                    error_occurred = True
            except ValueError:
                flash('Quantity must be a valid number.', 'error')
                error_occurred = True

        if not unit or len(unit.strip()) == 0:
            flash('Unit is required and cannot be empty.', 'error')
            error_occurred = True

        if not disposal_method: # Check if disposal_method is empty
            flash('Disposal method is required.', 'error')
            error_occurred = True

        if error_occurred:
            return render_template('edit_waste.html', entry=waste_entry_to_edit, form_data=form_data_for_template), 400

        try:
            waste_entry_to_edit.date = entry_date
            waste_entry_to_edit.waste_type = waste_type.strip() # Ensure strip
            waste_entry_to_edit.quantity = quantity
            waste_entry_to_edit.unit = unit.strip()
            waste_entry_to_edit.disposal_method = disposal_method.strip() # Ensure strip
            waste_entry_to_edit.notes = notes if notes else None

            db.session.commit()
            flash('Waste entry updated successfully!', 'success')
            return redirect(url_for('view_waste'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error when updating waste entry ID {id}: {e}")
            flash('An error occurred while updating the waste entry. Please try again.', 'error')
            return render_template('edit_waste.html', entry=waste_entry_to_edit, form_data=form_data_for_template), 500

    return render_template('edit_waste.html', entry=waste_entry_to_edit, form_data=None)

@app.route('/delete_waste/<int:id>', methods=['POST'])
def delete_waste(id):
    waste_entry_to_delete = WasteEntry.query.get_or_404(id)
    try:
        db.session.delete(waste_entry_to_delete)
        db.session.commit()
        flash('Waste entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting waste entry ID {id}: {e}")
        flash('An error occurred while deleting the waste entry. Please try again.', 'error')
    return redirect(url_for('view_waste'))

@app.route('/charts')
def charts():
    return render_template('charts.html')

@app.route('/api/resource_chart_data')
def resource_chart_data():
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        query = db.session.query(
            ResourceUsage.resource_type,
            func.sum(ResourceUsage.quantity).label('total_quantity')
        )

        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(ResourceUsage.date >= start_date)
            except ValueError:
                pass

        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(ResourceUsage.date <= end_date)
            except ValueError:
                pass

        query = query.group_by(ResourceUsage.resource_type).order_by(ResourceUsage.resource_type)
        aggregated_data = query.all()

        chart_data = {
            'labels': [item.resource_type for item in aggregated_data],
            'datasets': [{
                'label': 'Total Quantity Used',
                'data': [item.total_quantity for item in aggregated_data],
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.2)', 'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)', 'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)', 'rgba(255, 159, 64, 0.2)'
                ],
                'borderColor': [
                    'rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)', 'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)', 'rgba(255, 159, 64, 1)'
                ],
                'borderWidth': 1
            }]
        }
        return jsonify(chart_data)

    except Exception as e:
        app.logger.error(f"Error generating chart data: {e}")
        return jsonify({'error': str(e), 'labels': [], 'datasets': []}), 500

# --- CLI Commands ---
@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.create_all()
    print(f"Database initialized and tables created at: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    app.run(debug=True)
