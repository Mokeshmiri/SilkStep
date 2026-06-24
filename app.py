from flask import Flask, render_template, request, redirect, url_for, session
import tours_dao
import users_dao
import bookings_dao

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
def can_manage_tour(tour_id):
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return None

    role = session.get("user_role")
    user_id = session.get("user_id")

    # Admin: full access to any tour
    if role == "admin":
        return tour

    # Guide: only own tours
    if role == "guide" and tour["guide_id"] == user_id:
        return tour

    return None

@app.route("/") #route for the home page
def home():
    return render_template('home.html')

@app.route("/tours") #route for the tours page
def tours():
    db_tours = tours_dao.get_tours()
    sample_tours = [dict(row) for row in db_tours]
    return render_template("tour.html", tours=sample_tours)

@app.route("/signup")
def signup():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("txt_name")
    surname = request.form.get("txt_surname")
    email = request.form.get("txt_email")
    password = request.form.get("txt_password")
    role = request.form.get("txt_role")

    if users_dao.get_user_by_email(email):
        return "Email already registered", 400

    users_dao.new_user(name, surname, email, password, role)
    return redirect(url_for("home"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/do_login", methods=["POST"])
def do_login():
    email = request.form.get("txt_email")
    password = request.form.get("txt_password")

    user = users_dao.get_user_by_email(email)

    if not user or user["password"] != password:
        return render_template("login.html", error="Invalid email or password")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["user_role"] = user["role"]

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/guide/new-tour", methods=["GET", "POST"])
def new_tour():
    if session.get("user_role") != "guide":
        return redirect(url_for("home"))

    if request.method == "POST":
        tours_dao.create_tour(
            request.form.get("txt_title"),
            request.form.get("txt_schedule"),
            request.form.get("txt_duration"),
            request.form.get("txt_payment"),
            request.form.get("txt_summary"),
            session["user_id"]
        )
        return redirect(url_for("tours"))

    return render_template("new_tour.html")
@app.route("/guide/edit-tour/<int:tour_id>", methods=["GET", "POST"])
def edit_tour(tour_id):
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))

    if bookings_dao.tour_has_bookings(tour_id):
        return "This tour already has bookings and cannot be edited.", 400

    if request.method == "POST":
        tours_dao.update_tour(
            tour_id,
            request.form.get("txt_title"),
            request.form.get("txt_schedule"),
            request.form.get("txt_duration"),
            request.form.get("txt_payment"),
            request.form.get("txt_summary"),
        )
        return redirect(url_for("tours"))

    return render_template("edit_tour.html", tour=dict(tour))

@app.route("/guide/delete-tour/<int:tour_id>", methods=["POST"])
def delete_tour_route(tour_id):
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))

    if bookings_dao.tour_has_bookings(tour_id):
        return "This tour already has bookings and cannot be deleted.", 400

    tours_dao.delete_tour(tour_id)
    return redirect(url_for("tours"))

@app.route("/admin")
def admin_dashboard():
    if session.get("user_role") != "admin":
        return redirect(url_for("home"))

    stats = {
        "tours_count": tours_dao.count_tours(),
        "users_count": users_dao.count_users(),
        "guides_count": users_dao.count_by_role("guide"),
        "participants_count": users_dao.count_by_role("participant"),
    }
    return render_template("admin.html", stats=stats)
@app.route("/tour/<int:tour_id>")
def tour_detail(tour_id):
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404
    return render_template("tour_detail.html", tour=dict(tour))

@app.route("/tour/<int:tour_id>/book", methods=["POST"])
def book_tour(tour_id):
    if session.get("user_role") != "participant":
        return redirect(url_for("tour_detail", tour_id=tour_id))

    tour_date = request.form.get("txt_tour_date")
    if not tour_date:
        return redirect(url_for("tour_detail", tour_id=tour_id))

    bookings_dao.create_booking(
        tour_id=tour_id,
        participant_id=session["user_id"],
        tour_date=tour_date
    )
    return redirect(url_for("my_bookings"))

@app.route("/my-bookings")
def my_bookings():
    if session.get("user_role") != "participant":
        return redirect(url_for("home"))

    rows = bookings_dao.get_bookings_by_participant(session["user_id"])
    bookings = [dict(r) for r in rows]
    return render_template("my_bookings.html", bookings=bookings)

@app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    if session.get("user_role") != "participant":
        return redirect(url_for("home"))

    bookings_dao.cancel_booking(booking_id, session["user_id"])
    return redirect(url_for("my_bookings"))
    
if __name__ == '__main__':
    app.run(debug=True, port=5001)