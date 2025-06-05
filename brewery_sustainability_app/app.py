from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

app = Flask(__name__)

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
        all_resources = ResourceUsage.query.order_by(ResourceUsage.date.desc(), ResourceUsage.id.desc()).all()
    except Exception as e:
        app.logger.error(f"Error fetching resources: {e}")
        flash('Could not retrieve resource data from the database.', 'error')
        all_resources = []
    return render_template('view_resources.html', resources=all_resources)


# --- CLI Commands ---
@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.create_all()
    print(f"Database initialized and tables created at: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    app.run(debug=True)
