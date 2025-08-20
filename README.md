
# BusMate (Bus Student Bond)

A Flask + MySQL web application to manage **college bus routes** with dedicated **student** and **admin** portals.

## 🚀 Features
- **Student Portal**
  - Login and view bus assigned to their stop
- **Admin Portal**
  - Manage buses (add / delete / update)
  - Manage drivers (add / delete / update contact info)
  - Manage routes (assign buses to stops)

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Database:** MySQL
- **Frontend:** HTML, CSS, Bootstrap
- **Other:** Jinja2 templates

## 📂 Project Structure
```

project/
│── app.py              # Main Flask app
│── templates/          # HTML files
│── static/             # CSS, JS, images
│── requirements.txt    # Dependencies
│── README.md           # Project documentation

````

## ⚡ Installation & Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/busmate-flask.git
   cd busmate-flask
````

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Mac/Linux
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure MySQL database in `app.py` (update username, password, db name).

5. Run the app:

   ```bash
   flask run
   ```

6. Open in browser: `http://127.0.0.1:5000/`

## 📌 Future Enhancements

* Student bus tracking in real-time
* Notifications for route/bus changes
* Mobile app integration

---

✨ Made with ❤️ by Sneha Dadhich

````
