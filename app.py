from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import qrcode
import os

# Create an app instance
app = Flask(__name__)  
mysql = MySQL(app)


# configuring the mysql database
app.secret_key = '9f2c1f3d9b6f4c1d8c7e2a9a0e3b5f78' # If it's missing or weak, users can tamper with session data.
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Vasu__8088'  # Enter your MySql password 
app.config['MYSQL_DB'] = 'bus_student_bond'


ADMIN_CREDENTIALS = {'admin': 'admin123'}

# -------------------- ADMIN LOGIN --------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if ADMIN_CREDENTIALS.get(username) == password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            msg = 'Invalid credentials'
    return render_template('admin_login.html', msg=msg)

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('manage_bus.html')

@app.route('/admin/current_routes')
def current_routes():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('current_routes.html')

@app.route('/admin/manage_bus')
def manage_bus():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))  # redirect if not logged in

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT 
            DISTINCT b.bus_id,
            b.bus_number,
            d.driver_name,
            b.capacity
        FROM Bus b
        JOIN Bus_Route br ON b.bus_id = br.bus_id
        JOIN Driver d ON br.driver_id = d.driver_id;
    """)
    buses = cursor.fetchall()

    # Fetch drivers
    cursor.execute("SELECT driver_id, driver_name FROM Driver")
    drivers = cursor.fetchall()

    cursor.close()
    return render_template("manage_bus.html", buses=buses, drivers=drivers)


@app.route('/admin/manage_driver')
def manage_driver():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))  # redirect if not logged in

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT driver_id, driver_name, phone_number FROM Driver;
    """)
    drivers = cursor.fetchall()

    cursor.close()
    return render_template("manage_driver.html", drivers=drivers)

@app.route('/admin/mange_routes')
def manage_routes():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    bus_id = request.args.get('bus_id')  # get selected bus_id from query string

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if bus_id:
        cursor.execute("""
            SELECT 
                b.bus_id, b.bus_stop, b.arriving_time, b2.capacity, d.driver_name 
            FROM bus_route b
            LEFT JOIN driver d ON d.driver_id = b.driver_id
            LEFT JOIN bus b2 ON b2.bus_id = b.bus_id
            WHERE b.bus_id = %s;
        """, (bus_id,))
    else:
        cursor.execute("""
            SELECT 
                b.bus_id, b.bus_stop, b.arriving_time, b2.capacity, d.driver_name 
            FROM bus_route b
            LEFT JOIN driver d ON d.driver_id = b.driver_id
            LEFT JOIN bus b2 ON b2.bus_id = b.bus_id;
        """)
    bus_route_data = cursor.fetchall()

    cursor.execute("""SELECT DISTINCT bus_id FROM bus_route;""")
    buses = cursor.fetchall()
    cursor.close()

    return render_template(
        "manage_routes.html", 
        bus_route_data=bus_route_data, 
        buses=buses,
        selected_bus_id=bus_id  # to keep dropdown selected
    )


@app.route('/admin/change_routes')
def change_routes():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin.change_routes.html')


# -------------------- LOGIN --------------------
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            msg = 'Please fill out all fields.'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM student WHERE email = %s', (email,))
            account = cursor.fetchone()

            if account and check_password_hash(account['password'], password):
                session['loggedin'] = True
                # session['id'] = account['id']
                session['username'] = account['name']
                return redirect(url_for('buses_for_stop'))
            else:
                msg = 'Incorrect username or password.'
    return render_template('login.html', msg=msg)

# -------------------- LOGOUT --------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------- REGISTER --------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    bus_stops = ['Paota', 'Ratanada', 'AIIMS', 'MIA', 'Chopsani']
    msg = ''

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        department = request.form.get('department')
        year = request.form.get('year')
        bus_stop = request.form.get('bus_stop')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([student_id, name, department, year, bus_stop, email, password]):
            msg = 'Please fill out all fields.'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM student WHERE email = %s', (email,))
            account = cursor.fetchone()

            if account:
                msg = 'Account already exists!'
            else:
                hashed_password = generate_password_hash(password)
                query = """INSERT INTO student 
                           (student_id, name, department, year, bus_stop, email, password)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                values = (student_id, name, department, year, bus_stop, email, hashed_password)

                cursor.execute(query, values)
                mysql.connection.commit()
                msg = 'Registered successfully!'
            cursor.close()

    return render_template('register.html', msg=msg, bus_stops=bus_stops)

# -------------------- Student functions --------------------

# Folder to store generated QR codes
QR_FOLDER = 'static/qrcodes'
os.makedirs(QR_FOLDER, exist_ok=True)

def generate_qr(student_id):
    """Generate and save QR code image for a student."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(student_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(QR_FOLDER, f"{student_id}.png")
    img.save(r"qr_path")
    return qr_path

@app.route('/get_student_info/<student_id>')
def get_student_info(student_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM Student WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.close()

    if not student:
        return {'error': 'Student not found'}

    return {
        'name': student['name'],
        'department': student['department'],
        'bus_stop': student['bus_stop'],
        'route_no': student['route_no'],
        'fees_paid': bool(student['fees_paid'])
    }


@app.route('/bus_id')
def bus_id():
    return render_template('bus_id.html')


# ---------------- BUS ID ----------------
def generate_bus_id(student_id):
    img = qrcode.make(student_id)
    img.save(f"static/qrcodes/{student_id}.png")


# ---------------- BUS FINDER ----------------
@app.route('/stop', methods=['GET', 'POST'])
def buses_for_stop():
    # Get the selected stop from the request args (URL param)
    stop_name = request.args.get('stop_name')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Fetch all distinct bus stops for dropdown selection
    cursor.execute("SELECT DISTINCT bus_stop FROM Bus_Route")
    stops = [row['bus_stop'] for row in cursor.fetchall()]
    print(f"{stop_name}  :  {stops}")
    buses = []
    if stop_name:
        # Only query if stop_name is selected (avoid null fetch)
        cursor.execute("""
            SELECT b.bus_id, br.arriving_time, d.driver_name, d.phone_number, br.route_date
            FROM Bus_Route br
            JOIN Bus b ON br.bus_id = b.bus_id
            JOIN Driver d ON br.driver_id = d.driver_id
            WHERE br.bus_stop = %s
            ORDER BY br.route_date DESC, br.arriving_time ASC
        """, (stop_name,))
        buses = cursor.fetchall()

    return render_template('buses_for_stop.html', buses=buses, stops=stops, stop_name=stop_name)


# -------------------- DASHBOARD --------------------
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))


# -------------------- MAIN --------------------
if __name__ == '__main__':
    app.run(debug=True)


# -------------------- Test Info --------------------
# Sneha_Dadhich
# Sneha@11

# -------------------- To Do --------------------
# Currently the email is getting used as the id 
# so change the id to format JIET/DS/XX/XXX (like JIET/DS/22/030)
# here DS is the department Data Science and 030 is unique id