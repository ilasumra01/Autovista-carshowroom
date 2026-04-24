from flask import Flask, render_template, request, redirect, session
from db import get_db

app = Flask(__name__)
app.secret_key = "autovista123"


# ---------- WELCOME PAGE ----------
@app.route("/")
def welcome():
    return render_template("welcome.html")


# ---------- USER LOGIN PAGE ----------
@app.route("/login_page")
def login_page():
    return render_template("login.html")


# ---------- USER LOGIN ----------
@app.route("/login", methods=["POST"])
def login_user():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    u = request.form["username"]
    p = request.form["password"]

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
    user = cursor.fetchone()

    if user:
        session.clear()
        session["user"] = user["username"]
        session["user_id"] = user["id"]

        return redirect("/showroom")

    return "Invalid Login"


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        u = request.form["username"]
        e = request.form["email"]
        p = request.form["password"]
        ph = request.form["phone"]

        cursor.execute("SELECT * FROM users WHERE username=%s", (u,))
        if cursor.fetchone():
            return "Username already exists!"

        cursor.execute(
            "INSERT INTO users(username,email,password,phone) VALUES (%s,%s,%s,%s)",
            (u, e, p, ph)
        )
        db.commit()

        return redirect("/login_page")

    return render_template("register.html")


# ---------- ADMIN LOGIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u == "admin" and p == "admin123":
            session.clear()
            session["admin"] = True
            return redirect("/admin-dashboard")

        return "Invalid Admin Login"

    return render_template("admin_login.html")


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()

    return render_template("admin_dashboard.html", cars=cars)


# ---------- ADD CAR ----------
@app.route("/add-car", methods=["POST"])
def add_car():
    if "admin" not in session:
        return redirect("/admin")

    model = request.form["model"]
    price = request.form["price"]
    category = request.form["category"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO cars(model,price,category) VALUES(%s,%s,%s)",
        (model, price, category)
    )
    db.commit()

    return redirect("/admin-dashboard")


# ---------- DELETE CAR ----------
@app.route("/delete-car/<int:id>")
def delete_car(id):
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM cars WHERE id=%s", (id,))
    db.commit()

    return redirect("/admin-dashboard")

# ---------- REMOVE FROM CART ----------
@app.route("/remove/<int:id>")
def remove(id):
    if "user_id" not in session:
        return redirect("/login_page")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM cart WHERE id=%s", (id,))
    db.commit()

    return redirect("/cart")


# ---------- SHOWROOM (ALL PANELS) ----------
@app.route("/showroom")
def showroom():
    search = request.args.get("search")
    category = request.args.get("category")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM cars WHERE 1=1"
    params = []

    if search:
        query += " AND model LIKE %s"
        params.append("%" + search + "%")

    if category:
        query += " AND category=%s"
        params.append(category)

    cursor.execute(query, params)
    cars = cursor.fetchall()

    is_user = "user_id" in session
    is_admin = "admin" in session

    return render_template("showroom.html", cars=cars, is_user=is_user, is_admin=is_admin)


# ---------- ADD CART ----------
@app.route("/add_cart/<int:id>")
def add_cart(id):
    if "user_id" not in session:
        return redirect("/login_page")

    db = get_db()
    cur = db.cursor()

    cur.execute("INSERT INTO cart(user_id,car_id) VALUES(%s,%s)",
                (session["user_id"], id))
    db.commit()

    return redirect("/showroom")


# ---------- CART ----------
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login_page")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
    SELECT cart.id,cars.model,cars.price
    FROM cart
    JOIN cars ON cart.car_id=cars.id
    WHERE cart.user_id=%s
    """, (session["user_id"],))

    items = cur.fetchall()

    total = 0
    for i in items:
        price = float(i["price"].split()[0])
        total += price

    return render_template("cart.html", items=items, total=total)


# ---------- TEST DRIVE ----------
@app.route("/test-drive", methods=["GET", "POST"])
def test_drive():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        car = request.form["car"]
        date = request.form["date"]
        time = request.form["time"]

        cursor.execute(
            "INSERT INTO test_drive(name, car, date, time) VALUES (%s,%s,%s,%s)",
            (name, car, date, time)
        )
        db.commit()

        return "Booking Successful!"

    cursor.execute("SELECT model FROM cars")
    cars = cursor.fetchall()

    return render_template("test_drive.html", cars=cars)

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ---------- CONTACT FORM ----------
@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    name = request.form["name"]
    email = request.form["email"]
    subject = request.form["subject"]
    message = request.form["message"]

    # Optional: store in database
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO contact(name,email,subject,message) VALUES (%s,%s,%s,%s)",
        (name, email, subject, message)
    )
    db.commit()

    return "Message Sent Successfully!"

@app.route("/details/<int:id>")
def details(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cars WHERE id=%s", (id,))
    car = cursor.fetchone()

    return render_template("details.html", car=car)


# ---------- EMI ----------
@app.route("/emi", methods=["GET", "POST"])
def emi():
    emi = None

    if request.method == "POST":
        p = float(request.form["price"])
        r = float(request.form["rate"]) / 12 / 100
        t = int(request.form["time"]) * 12

        emi = (p * r * (1 + r)**t) / ((1 + r)**t - 1)

    return render_template("emi.html", emi=emi)

# ---------- BUY CAR ----------
@app.route("/buy/<int:id>")
def buy(id):
    if "user_id" not in session:
        return redirect("/login_page")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cars WHERE id=%s", (id,))
    car = cursor.fetchone()

    return render_template("buy.html", car=car)

@app.route("/feedback")
@app.route("/feedback/<int:car_id>")
def feedback(car_id=None):
    return render_template("feedback.html", car_id=car_id)

# ---------- submit feedback ----------
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    name = request.form["name"]
    email = request.form["email"]
    rating = request.form["rating"]
    message = request.form["message"]
    car_id = request.form["car_id"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO feedback(name,email,rating,message,car_id) VALUES (%s,%s,%s,%s,%s)",
        (name, email, rating, message, car_id)
    )
    db.commit()

    return "Feedback Submitted Successfully!"


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
