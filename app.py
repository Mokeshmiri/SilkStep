"""main flask routes for the silkstep web application."""

import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import tours_dao
import users_dao
import bookings_dao
import tour_photos_dao

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

AVAILABLE_LANGUAGES = [
    "English",
    "Italian",
    "Persian",
    "French",
    "Spanish",
]

ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_photo(filename):
    """check uploaded file extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS


def save_tour_photo(file, tour_id):
    """save uploaded tour image in static/uploads and return relative path."""
    if not file or not file.filename:
        return ""
    if not allowed_photo(file.filename):
        return ""

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique = uuid.uuid4().hex[:8]
    filename = secure_filename(f"tour_{tour_id}_{unique}.{ext}")
    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f"uploads/{filename}"


def remove_photo_file(photo_path):
    """delete an uploaded image from disk if it exists."""
    if not photo_path or photo_path.startswith("http://") or photo_path.startswith("https://"):
        return
    file_path = os.path.join(app.root_path, "static", photo_path)
    if os.path.exists(file_path):
        os.remove(file_path)


def save_uploaded_photos(tour_id, files):
    """save up to MAX photos per tour and return list of saved relative paths."""
    saved_paths = []
    for file in files:
        if tour_photos_dao.count_photos_for_tour(tour_id) >= tour_photos_dao.MAX_PHOTOS_PER_TOUR:
            break
        photo_path = save_tour_photo(file, tour_id)
        if photo_path:
            tour_photos_dao.add_photo(tour_id, photo_path)
            saved_paths.append(photo_path)
    return saved_paths


def sync_tour_cover_photo(tour_id):
    """keep tours.photo_url aligned with the first gallery photo for list cards."""
    photos = tour_photos_dao.get_photos_for_tour(tour_id)
    cover = photos[0]["photo_path"] if photos else ""
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return
    tours_dao.update_tour(
        tour_id,
        tour["title"],
        tour["schedule"],
        tour["duration"],
        tour["payment"],
        tour["summary"],
        cover,
        tour["meeting_point"] or "",
        tour["meeting_map_link"] or "",
        tour["max_participants"] or 15,
    )


def tour_photo_src(photo_url):
    """return browser-ready image path for local uploads or old external urls."""
    if not photo_url:
        return ""
    if photo_url.startswith("http://") or photo_url.startswith("https://"):
        return photo_url
    return url_for("static", filename=photo_url)


def tour_dict(row):
    """convert sqlite row to dict and add photo_src for templates."""
    data = dict(row)
    photos = tour_photos_dao.get_photos_for_tour(data["id"])
    if photos:
        data["photo_src"] = tour_photo_src(photos[0]["photo_path"])
    else:
        data["photo_src"] = tour_photo_src(data.get("photo_url"))
    return data

def can_manage_tour(tour_id):
    """return the tour only when current user is allowed to manage it."""
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return None

    role = session.get("user_role")
    user_id = session.get("user_id")

    # admin can manage any tour
    if role == "admin":
        return tour

    # guide can manage only their own tours
    if role == "guide" and tour["guide_id"] == user_id:
        return tour

    return None

# home page with featured tours
@app.route("/")
def home():
    db_tours = tours_dao.get_tours()
    tours = [tour_dict(row) for row in db_tours]
    return render_template('home.html', tours=tours)

# public tours list page
@app.route("/tours")
def tours():
    selected_language = request.args.get("language", "")
    if selected_language and selected_language not in AVAILABLE_LANGUAGES:
        selected_language = ""

    if selected_language:
        db_tours = tours_dao.get_tours_by_language(selected_language)
    else:
        db_tours = tours_dao.get_tours()

    sample_tours = [tour_dict(row) for row in db_tours]
    return render_template(
        "tour.html",
        tours=sample_tours,
        available_languages=AVAILABLE_LANGUAGES,
        selected_language=selected_language,
    )
@app.route("/signup")
def signup():
    """show participant/guide/admin registration form."""
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    """create a user account after basic duplicate-email validation."""
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
    """show login form."""
    return render_template("login.html")

@app.route("/do_login", methods=["POST"])
def do_login():
    """authenticate user and store role/session fields."""
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
    """clear the current session."""
    session.clear()
    return redirect(url_for("home"))

@app.route("/guide/new-tour", methods=["GET", "POST"])
def new_tour():
    """guide-only page to create a tour with one or more languages."""
    if session.get("user_role") != "guide":
        return redirect(url_for("home"))
    
    if request.method == "POST":
        selected_languages = request.form.getlist("txt_languages")
        selected_languages = [l for l in selected_languages if l in AVAILABLE_LANGUAGES]

        if not selected_languages:
            return "Select at least one language", 400

        try:
            max_participants = int(request.form.get("txt_max_participants", "15"))
        except (TypeError, ValueError):
            max_participants = 15
        max_participants = max(1, max_participants)

        tour_id = tours_dao.create_tour(
            request.form.get("txt_title"),
            request.form.get("txt_schedule"),
            request.form.get("txt_duration"),
            request.form.get("txt_payment"),
            request.form.get("txt_summary"),
            "",
            request.form.get("txt_meeting_point", "").strip(),
            request.form.get("txt_meeting_map_link", "").strip(),
            max_participants,
            session["user_id"]
        )
        save_uploaded_photos(tour_id, request.files.getlist("txt_photos"))
        sync_tour_cover_photo(tour_id)
        tours_dao.set_tour_languages(tour_id, selected_languages)
        return redirect(url_for("tours"))

    return render_template("new_tour.html", available_languages=AVAILABLE_LANGUAGES)

@app.route("/guide/edit-tour/<int:tour_id>", methods=["GET", "POST"])
def edit_tour(tour_id):
    """guide/admin edit flow with booking lock and language update."""
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))

    if bookings_dao.tour_has_bookings(tour_id):
        return "This tour already has bookings and cannot be edited.", 400

    if request.method == "POST":
        selected_languages = request.form.getlist("txt_languages")
        selected_languages = [l for l in selected_languages if l in AVAILABLE_LANGUAGES]

        if not selected_languages:
            return "Select at least one language", 400

        try:
            max_participants = int(request.form.get("txt_max_participants", "15"))
        except (TypeError, ValueError):
            max_participants = 15
        max_participants = max(1, max_participants)

        tours_dao.update_tour(
            tour_id,
            request.form.get("txt_title"),
            request.form.get("txt_schedule"),
            request.form.get("txt_duration"),
            request.form.get("txt_payment"),
            request.form.get("txt_summary"),
            tour["photo_url"] or "",
            request.form.get("txt_meeting_point", "").strip(),
            request.form.get("txt_meeting_map_link", "").strip(),
            max_participants,
        )
        save_uploaded_photos(tour_id, request.files.getlist("txt_photos"))
        sync_tour_cover_photo(tour_id)
        tours_dao.set_tour_languages(tour_id, selected_languages)
        return redirect(url_for("tours"))

    tour_data = dict(tour)
    tour_data["languages_list"] = tours_dao.get_languages_for_tour(tour_id)
    photos = [dict(p) for p in tour_photos_dao.get_photos_for_tour(tour_id)]
    return render_template(
        "edit_tour.html",
        tour=tour_data,
        photos=photos,
        max_photos=tour_photos_dao.MAX_PHOTOS_PER_TOUR,
        available_languages=AVAILABLE_LANGUAGES,
    )

@app.route("/guide/delete-tour/<int:tour_id>", methods=["POST"])
def delete_tour_route(tour_id):
    """delete a tour only when authorized and no bookings exist."""
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))

    if bookings_dao.tour_has_bookings(tour_id):
        return "This tour already has bookings and cannot be deleted.", 400

    for photo in tour_photos_dao.get_photos_for_tour(tour_id):
        remove_photo_file(photo["photo_path"])
    remove_photo_file(dict(tour).get("photo_url"))
    tours_dao.delete_tour(tour_id)
    return redirect(url_for("tours"))


@app.route("/guide/tour-photo/<int:photo_id>/delete", methods=["POST"])
def delete_tour_photo(photo_id):
    """guide/admin deletes one gallery photo."""
    if session.get("user_role") not in ("guide", "admin"):
        return redirect(url_for("home"))

    photo = tour_photos_dao.get_photo_by_id(photo_id)
    if not photo:
        return redirect(url_for("tours"))

    tour = can_manage_tour(photo["tour_id"])
    if not tour:
        return redirect(url_for("tours"))

    if bookings_dao.tour_has_bookings(photo["tour_id"]):
        return "This tour already has bookings and cannot be edited.", 400

    remove_photo_file(photo["photo_path"])
    tour_photos_dao.delete_photo(photo_id)
    sync_tour_cover_photo(photo["tour_id"])
    return redirect(url_for("edit_tour", tour_id=photo["tour_id"]))

@app.route("/admin")
def admin_dashboard():
    """simple admin dashboard with high-level counters."""
    if session.get("user_role") != "admin":
        return redirect(url_for("home"))

    stats = {
        "tours_count": tours_dao.count_tours(),
        "users_count": users_dao.count_users(),
        "guides_count": users_dao.count_by_role("guide"),
        "participants_count": users_dao.count_by_role("participant"),
        "bookings_count": bookings_dao.count_bookings(),
    }
    return render_template("admin.html", stats=stats)
@app.route("/tour/<int:tour_id>")
def tour_detail(tour_id):
    """tour detail page used by participants before booking."""
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404

    tour_data = dict(tour)
    langs = tours_dao.get_languages_for_tour(tour_id)
    tour_data["languages"] = ", ".join(langs) if langs else "Not set"
    photos = [dict(p) for p in tour_photos_dao.get_photos_for_tour(tour_id)]
    if photos:
        tour_data["photo_src"] = tour_photo_src(photos[0]["photo_path"])
    else:
        tour_data["photo_src"] = tour_photo_src(tour_data.get("photo_url"))

    booking_error = request.args.get("booking_error", "")
    return render_template(
        "tour_detail.html",
        tour=tour_data,
        photos=photos,
        booking_error=booking_error,
    )
    
@app.route("/tour/<int:tour_id>/book", methods=["POST"])
def book_tour(tour_id):
    """participant booking endpoint with party size and optional notes."""
    if session.get("user_role") != "participant":
        return redirect(url_for("tour_detail", tour_id=tour_id))

    tour_date = request.form.get("txt_tour_date")
    party_size_raw = request.form.get("txt_party_size", "1")
    notes = request.form.get("txt_notes", "").strip()

    if not tour_date:
        return redirect(url_for("tour_detail", tour_id=tour_id))

    # keep this safe parsing to avoid bad numeric input
    try:
        party_size = int(party_size_raw)
    except (TypeError, ValueError):
        party_size = 1
    party_size = max(1, party_size)

    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404

    max_participants = tour["max_participants"] or 15
    already_booked = bookings_dao.get_booked_spots(tour_id, tour_date)
    remaining = max_participants - already_booked

    if party_size > remaining:
        msg = f"Only {remaining} spot(s) left on that date."
        return redirect(
            url_for("tour_detail", tour_id=tour_id, booking_error=msg)
        )
    

    bookings_dao.create_booking(
        tour_id=tour_id,
        participant_id=session["user_id"],
        tour_date=tour_date,
        party_size=party_size,
        notes=notes,
    )
    return redirect(url_for("my_bookings"))

@app.route("/my-bookings")
def my_bookings():
    """participant page listing only their own bookings."""
    if session.get("user_role") != "participant":
        return redirect(url_for("home"))

    rows = bookings_dao.get_bookings_by_participant(session["user_id"])
    bookings = [dict(r) for r in rows]
    return render_template("my_bookings.html", bookings=bookings)

@app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    """participant cancellation endpoint for their own booking ids."""
    if session.get("user_role") != "participant":
        return redirect(url_for("home"))

    bookings_dao.cancel_booking(booking_id, session["user_id"])
    return redirect(url_for("my_bookings"))

@app.route("/guide/bookings")
def guide_bookings():
    """guide page listing only their own bookings."""
    if session.get("user_role") != "guide":
        return redirect(url_for("home"))

    rows = bookings_dao.get_bookings_by_guide(session["user_id"])
    bookings = [dict(r) for r in rows]
    return render_template("guide_bookings.html", bookings=bookings)

@app.route("/tour/<int:tour_id>/availability")
def tour_availability(tour_id):
  """return json with spots left for one date (used by booking form)."""
  tour = tours_dao.get_tour_by_id(tour_id)
  if not tour:
    return {"error": "Tour not found"}, 404

  tour_date = request.args.get("date", "")
  if not tour_date:
    return {"error": "date required"}, 400

  max_participants = tour["max_participants"] or 15
  booked = bookings_dao.get_booked_spots(tour_id, tour_date)
  remaining = max(0, max_participants - booked)

  return {
    "max": max_participants,
    "booked": booked,
    "remaining": remaining,
  }







if __name__ == '__main__':
    app.run(debug=True, port=5001)