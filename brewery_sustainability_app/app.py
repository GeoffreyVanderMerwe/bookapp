from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
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

    return render_template('add_resource.html', form_data=form_data_to_render)

@app.route('/view_resources')
def view_resources():
    try:
        # Get filter/sort parameters from request arguments
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        resource_type_filter = request.args.get('resource_type')
        sort_by = request.args.get('sort_by', 'date') # Default sort by date
        sort_order = request.args.get('sort_order', 'desc') # Default sort order descending

        query = ResourceUsage.query

        # Apply filters
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

        if resource_type_filter and resource_type_filter != "": # "" means 'All Types'
            query = query.filter(ResourceUsage.resource_type == resource_type_filter)

        # Apply sorting
        sort_column = ResourceUsage.date # Default sort column
        if sort_by == 'resource_type':
            sort_column = ResourceUsage.resource_type
        elif sort_by == 'quantity':
            sort_column = ResourceUsage.quantity

        if sort_order == 'asc':
            query = query.order_by(sort_column.asc(), ResourceUsage.id.asc())
        else: # Default to descending
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
    resource_to_edit = ResourceUsage.query.get_or_404(id) # get_or_404 is convenient

    if request.method == 'POST':
        form_data_for_template = request.form # Preserve form data for re-rendering on error
        date_str = request.form.get('date')
        resource_type = request.form.get('resource_type')
        quantity_str = request.form.get('quantity')
        unit = request.form.get('unit')

        # Validation (similar to add_resource)
        if not date_str:
            flash('Date is required.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400
        try:
            entry_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400

        if not resource_type:
            flash('Resource type is required.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400

        if not quantity_str:
            flash('Quantity is required.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                flash('Quantity must be a positive number.', 'error')
                return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400
        except ValueError:
            flash('Quantity must be a valid number.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400

        if not unit or len(unit.strip()) == 0:
            flash('Unit is required and cannot be empty.', 'error')
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 400

        # If all validation passes:
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
            # Pass original resource and current (failed) form data back to template
            return render_template('edit_resource.html', resource=resource_to_edit, form_data=form_data_for_template), 500

    # For GET request, render the form with the existing resource data
    return render_template('edit_resource.html', resource=resource_to_edit, form_data=None)
@app.route('/delete_resource/<int:id>', methods=['POST'])
def delete_resource(id):
    resource_to_delete = ResourceUsage.query.get_or_404(id) # Fetches or returns 404 if not found
    try:
        db.session.delete(resource_to_delete)
        db.session.commit()
        flash('Resource usage entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting resource ID {id}: {e}")
        flash('An error occurred while deleting the entry. Please try again.', 'error')
    return redirect(url_for('view_resources'))
# --- CLI Commands ---
@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.create_all()
    print(f"Database initialized and tables created at: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    app.run(debug=True)
