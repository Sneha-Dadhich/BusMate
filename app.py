from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from datetime import datetime, date
from io import BytesIO
import MySQLdb.cursors
import re
import qrcode
import os
import math

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
            return redirect(url_for('manage_bus'))
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
            DISTINCT(Bus.bus_id), 
            Bus.bus_number, 
            Driver.driver_name
        FROM Bus
        LEFT JOIN Bus_Route ON Bus.bus_id = Bus_Route.bus_id
        LEFT JOIN Driver ON Bus_Route.driver_id = Driver.driver_id;
    """)
    buses = cursor.fetchall()

    cursor.close()
    return render_template("manage_bus.html", buses=buses)

# ------ manage bus functions ------- 

@app.route("/get_drivers", methods=["GET"])
def get_drivers():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT driver_name FROM driver")
    drivers = cursor.fetchall()
    cursor.close()

    driver_list = [d[0] for d in drivers]
    return jsonify({"drivers": driver_list})

@app.route("/add_bus", methods=["POST", "GET"])
def add_bus():

    today = date.today()

    data = request.get_json()
    busID = data.get("busID")
    bus_number = data.get("bus_number")
    busCapacity = data.get("busCapacity")
    driver_name = data.get("driver_name")

    if not bus_number or not driver_name:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    try:
        cursor = mysql.connection.cursor()

        # Insert into bus table
        insert_bus = """
            INSERT INTO bus (bus_id, bus_number, capacity)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_bus, (busID, bus_number, busCapacity))
        mysql.connection.commit()

        # Fetch driver ID by name
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT driver_id FROM Driver WHERE driver_name = %s", (driver_name,))
        driver_row = cursor.fetchone()

        if not driver_row:
            return jsonify({"success": False, "message": "Driver not found"}), 404

        driver_id = driver_row["driver_id"]

        # Insert default route entry
        insert_route = """
            INSERT INTO Bus_Route (bus_id, bus_stop, arriving_time, route_date, driver_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_route, (busID, "JIET", "08:39:00", today, driver_id))
        mysql.connection.commit()

        return jsonify({"success": True, "message": "Bus added successfully"}), 200

    except Exception as e:
        print("Error adding bus:", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/delete_bus', methods=['POST'])
def delete_bus():
    data = request.get_json()
    bus_id = data.get('bus_id')

    try:
        cursor = mysql.connection.cursor()

        # ✅ Step 1: Delete routes using this bus
        cursor.execute("DELETE FROM Bus_Route WHERE bus_id = %s", (bus_id,))

        # ✅ Step 2: Delete the bus
        cursor.execute("DELETE FROM Bus WHERE bus_id = %s", (bus_id,))

        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})

    except Exception as e:
        print("Error deleting bus:", e)
        return jsonify({'success': False, 'message': str(e)})

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

# ------ manage driver functions ------- 

@app.route('/add_driver', methods=['POST', 'GET'])
def add_driver():
    data = request.get_json()

    driver_name = data.get("driver_name")
    phone_number = data.get("phone_number")

    if not driver_name or not phone_number:
        return jsonify({"success": False, "message": "Driver name and phone number are required"}), 400

    try:
        cursor = mysql.connection.cursor()

        query = "INSERT INTO Driver (driver_name, phone_number) VALUES (%s, %s)"
        cursor.execute(query, (driver_name, phone_number))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"success": True, "message": "Driver added successfully!"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



@app.route('/delete_driver', methods=['POST'])
def delete_driver():
    data = request.get_json()
    driver_id = data.get('driver_id')

    try:
        cursor = mysql.connection.cursor()

        # ✅ First, delete routes using that driver
        cursor.execute("DELETE FROM Bus_Route WHERE driver_id = %s", (driver_id,))
        
        # ✅ Then, delete the driver
        cursor.execute("DELETE FROM Driver WHERE driver_id = %s", (driver_id,))
        
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})

    except Exception as e:
        print("Error deleting driver:", e)
        return jsonify({'success': False, 'message': str(e)})


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

# ------ manage routes functions ------- 

@app.route("/get_bus_stops")
def get_bus_stops():
    cursor = mysql.connection.cursor()

    # Fetch distinct stops
    cursor.execute("SELECT DISTINCT bus_stop FROM bus_route ORDER BY bus_stop ASC")
    stops = [row[0] for row in cursor.fetchall()]

    cursor.close()

    return jsonify({"stops": stops})

@app.route('/add_route', methods=['POST', 'GET'])
def add_route():
    if request.method == 'GET':
        return "This endpoint only accepts POST JSON requests."
    
    data = request.get_json()
    print(f"Received data: {data}")

    bus_id = data.get("bus_id")
    bus_stop = data.get("bus_stop")
    arriving_time = data.get("arriving_time")
    route_date = data.get("route_date")
    driver_name = data.get("driver_name")

    if not bus_id or not bus_stop:
        return jsonify({"success": False, "message": "Bus ID and Bus Stop are required"}), 400

    # Validate optional fields
    if route_date:
        try:
            datetime.strptime(route_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "message": "route_date must be YYYY-MM-DD"}), 400

    if arriving_time:
        try:
            datetime.strptime(arriving_time, "%H:%M")
        except ValueError:
            return jsonify({"success": False, "message": "arriving_time must be HH:MM"}), 400

    try:

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT driver_id FROM Driver WHERE driver_name = %s", (driver_name,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"success": False, "message": "Driver not found"}), 404

        driver_id = result["driver_id"]


        cursor = mysql.connection.cursor()
        query = """
            INSERT INTO Bus_Route (bus_id, bus_stop, arriving_time, route_date, driver_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (bus_id, bus_stop, arriving_time, route_date, driver_id))
        mysql.connection.commit()
        route_id = cursor.lastrowid
        cursor.close()

        return jsonify({"success": True, "message": "Route added successfully!", "route_id": route_id})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    
@app.route('/delete_route', methods=['POST'])
def delete_route():
    data = request.get_json()
    bus_id = data.get('bus_id')
    bus_stop = data.get('bus_stop')
    print(f"Bus Stop : {bus_stop} \n bus id : {bus_id}")
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM bus_route WHERE bus_id = %s AND bus_stop = %s", (bus_id, bus_stop))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        print("Error deleting record:", e)
        return jsonify({'success': False, 'message': str(e)})

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
            cursor.execute('SELECT * FROM Student WHERE email = %s', (email,))
            account = cursor.fetchone()

            if account and check_password_hash(account['password'], password):
                session['loggedin'] = True
                session['student_id'] = account['student_id']
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
    msg = ''

    # Fetch bus stops
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
            SELECT DISTINCT bus_stop
            FROM bus_route 
            ORDER BY bus_stop
        """)
    bus_stops = cursor.fetchall()
    cursor.close()

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

                clean_id = student_id.replace('/', '')
                image_path = f"images/students_profile/{clean_id}.jpg"

                # -------------------------
                # Generate QR Code
                # -------------------------
                qr_data = (
                    f"ID: {student_id}\n"
                    f"Name: {name}\n"
                    f"Dept: {department}\n"
                    f"Year: {year}\n"
                    f"Bus Stop: {bus_stop}\n"
                    f"Email: {email}"
                )

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=4
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                qr_folder = "static/qr_codes"
                if not os.path.exists(qr_folder):
                    os.makedirs(qr_folder)

                qr_filename = f"{qr_folder}/{clean_id}.png"
                img.save(qr_filename)

                # -------------------------
                # Insert student with QR path
                # -------------------------
                query = """
                    INSERT INTO student 
                    (student_id, name, department, year, bus_stop, email, password, image_path, qr_code_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                values = (
                    student_id, name, department, year,
                    bus_stop, email, hashed_password,
                    image_path, qr_filename
                )

                cursor.execute(query, values)
                mysql.connection.commit()
                msg = 'Registered successfully!'

            cursor.close()

    return render_template('register.html', msg=msg, bus_stops=bus_stops)

# -------------------- bus tracking system --------------------
# -------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Distance between 2 GPS points in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi/2)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def timedelta_to_time_string(td):
    total_seconds = int(td.total_seconds())
    hours = (total_seconds // 3600) % 24
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


# -------------------------------------------------------------
# Data Access Layer
# -------------------------------------------------------------

class DB:

    # get live GPS for bus
    def get_live_location(self, bus_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT latitude, longitude FROM live_location WHERE bus_id=%s", (bus_id,))
        row = cursor.fetchone()
        cursor.close()

        if row:
            return type("Obj", (object,), {"lat": row[0], "lng": row[1]})
        else:
            return None

    # get list of stops with coordinates + order
    def get_stops(self, bus_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT stop_order, stop_name, latitude, longitude 
            FROM bus_stop_coordinates 
            WHERE bus_id=%s 
            ORDER BY stop_order
        """, (bus_id,))
        rows = cursor.fetchall()
        cursor.close()

        stops = []
        for row in rows:
            stops.append(
                type("Stop", (object,), {
                    "stop_order": row[0],
                    "stop_name": row[1],
                    "lat": row[2],
                    "lng": row[3]
                })
            )
        return stops


db = DB()


# -------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------

# HTML page
@app.route('/track_bus')
def track_bus_page():
    return render_template('track_bus.html')


# list buses for dropdown
@app.route('/get_buses')
def get_buses():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT bus_id FROM bus")
    result = cursor.fetchall()
    cursor.close()

    bus_ids = [row[0] for row in result]
    return jsonify({"bus_ids": bus_ids})


# timetable route
@app.route("/current_location/<bus_id>")
def current_location(bus_id):
    cursor = mysql.connection.cursor()

    # Fetch route info
    query = """
        SELECT br.bus_stop, br.arriving_time, sc.latitude, sc.longitude, sc.stop_order
        FROM Bus_Route br
        LEFT JOIN bus_stop_coordinates sc 
        ON br.bus_id = sc.bus_id AND br.bus_stop = sc.stop_name
        WHERE br.bus_id = %s
        ORDER BY sc.stop_order
    """
    cursor.execute(query, (bus_id,))
    rows = cursor.fetchall()

    # Fetch live location
    cursor.execute("SELECT latitude, longitude FROM live_location WHERE bus_id=%s", (bus_id,))
    live = cursor.fetchone()
    cursor.close()

    stops = []

    if not rows:
        # No route/stops found
        return jsonify({"stops": [{"stop_name": "No stops found", "arrival_time": "-", "status": "Not Available"}]})

    if not live:
        # Live location missing → mark all stops as Not Available
        for row in rows:
            stop_name, arriving_time, lat, lng, order = row
            stops.append({
                "stop_name": stop_name,
                "arrival_time": str(arriving_time) if arriving_time else "-",
                "status": "Not Available"
            })
        return jsonify({"stops": stops})

    # Live location exists → classify normally
    live_lat, live_lng = live
    min_dist = float('inf')
    current_order = None

    for row in rows:
        stop_name, arriving_time, lat, lng, order = row
        if lat is None or lng is None:
            continue  # skip stops without coordinates
        dist = haversine(live_lat, live_lng, lat, lng)
        if dist < min_dist:
            min_dist = dist
            current_order = order

    for row in rows:
        stop_name, arriving_time, lat, lng, order = row
        if lat is None or lng is None or current_order is None:
            status = "Not Available"
        elif order < current_order:
            status = "Passed"
        elif order == current_order:
            status = "Current"
        else:
            status = "Upcoming"

        stops.append({
            "stop_name": stop_name,
            "arrival_time": str(arriving_time) if arriving_time else "-",
            "status": status
        })

    return jsonify({"stops": stops})


# classify stops as passed / current / upcoming
@app.route("/bus_status/<bus_id>")
def bus_status(bus_id):
    # 1. live bus GPS
    live = db.get_live_location(bus_id)
    if live is None:
        return jsonify({"error": "No live location found"}), 404

    # 2. fetch all stops
    stops = db.get_stops(bus_id)
    if not stops:
        return jsonify({"error": "No stops found"}), 404

    min_dist = float("inf")
    current_order = None

    # 3. find nearest stop
    for stop in stops:
        dist = haversine(live.lat, live.lng, stop.lat, stop.lng)
        if dist < min_dist:
            min_dist = dist
            current_order = stop.stop_order

    result = []

    # 4. classify
    for stop in stops:
        if stop.stop_order < current_order:
            status = "passed"
        elif stop.stop_order == current_order:
            status = "current"
        else:
            status = "upcoming"

        result.append({
            "stop_name": stop.stop_name,
            "stop_order": stop.stop_order,
            "status": status
        })

    return jsonify(result)


# driver sending live location
@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json
    bus_id = data["bus_id"]
    lat = data["lat"]
    lng = data["lng"]

    print(f"bus id : {bus_id}")
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO live_location (bus_id, latitude, longitude)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            latitude=VALUES(latitude),
            longitude=VALUES(longitude)
    """, (bus_id, lat, lng))

    mysql.connection.commit()
    cursor.close()

    return jsonify({"status": "updated"})

# -------------------- Student functions --------------------

# # Folder to store generated QR codes
# QR_FOLDER = 'static/qrcodes'
# os.makedirs(QR_FOLDER, exist_ok=True)

# def generate_qr(student_id):
#     """Generate and save QR code image for a student."""
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(student_id)
#     qr.make(fit=True)

#     img = qr.make_image(fill_color="black", back_color="white")
#     qr_path = os.path.join(QR_FOLDER, f"{student_id}.png")
#     img.save(r"qr_path")
#     return qr_path

@app.route('/bus_id', methods=['GET', 'POST'])
def bus_id():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM student WHERE student_id = %s', (session['student_id'],))
    student_data = cursor.fetchone()
    cursor.close()

    if student_data:
        # ✅ Extract only the part after 'static\' or 'static/'
        path = student_data['image_path']
        path = "static/" + student_data['image_path']
        print(f"path : {path}")
        if 'static\\' in path:
            student_data['image_path'] = path.split('static\\')[-1].replace('\\', '/')
            print(f"student_data['image_path'] : {student_data['image_path']}")
        elif 'static/' in path:
            student_data['image_path'] = path.split('static/')[-1]
        else:
            # ✅ Corrected folder
            student_data['image_path'] = f"images/students_profile/default.jpg"


    return render_template('bus_id.html', student=student_data)

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