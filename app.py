import os
import uuid

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.utils import secure_filename

import bookings_dao
import tour_photos_dao
import tours_dao
import users_dao
import tour_stops_dao
from user_model import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"

# flask-login setup — loads user from db on each request
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    # reload user from db when flask-login reads the session cookie
    row = users_dao.get_user_by_id(int(user_id))
    return User(row) if row else None


AVAILABLE_LANGUAGES = ["English", "Italian", "Persian", "French", "Spanish"]
ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


# --- photo helpers ---

def allowed_photo(filename):
    # block weird file types on upload
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS


def save_tour_photo(file, tour_id):
    # save one image to static/uploads, return path like uploads/tour_3_abc.jpg
    if not file or not file.filename or not allowed_photo(file.filename):
        return ""
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique = uuid.uuid4().hex[:8]
    filename = secure_filename(f"tour_{tour_id}_{unique}.{ext}")
    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f"uploads/{filename}"


def remove_photo_file(photo_path):
    # delete file from disk when removing a gallery photo
    if not photo_path or photo_path.startswith("http"):
        return
    file_path = os.path.join(app.root_path, "static", photo_path)
    if os.path.exists(file_path):
        os.remove(file_path)


def save_uploaded_photos(tour_id, files):
    # loop file input — stops at 5 photos per tour
    for file in files:
        if tour_photos_dao.count_photos_for_tour(tour_id) >= tour_photos_dao.MAX_PHOTOS_PER_TOUR:
            break
        photo_path = save_tour_photo(file, tour_id)
        if photo_path:
            tour_photos_dao.add_photo(tour_id, photo_path)


def sync_tour_cover_photo(tour_id):
    # first gallery photo becomes the card thumbnail on home/tours
    photos = tour_photos_dao.get_photos_for_tour(tour_id)
    cover = photos[0]["photo_path"] if photos else ""
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return
    tours_dao.update_tour(
        tour_id,
        tour["title"], tour["schedule"], tour["duration"], tour["payment"], tour["summary"],
        cover, tour["meeting_point"] or "", tour["meeting_map_link"] or "", tour["max_participants"] or 15,
    )


def tour_photo_src(photo_url):
    # turn db path into full url for img src
    if not photo_url:
        return ""
    if photo_url.startswith("http"):
        return photo_url
    return url_for("static", filename=photo_url)


def tour_dict(row):
    # add photo_src for tour cards on home/tours pages
    data = dict(row)
    photos = tour_photos_dao.get_photos_for_tour(data["id"])
    if photos:
        data["photo_src"] = tour_photo_src(photos[0]["photo_path"])
    else:
        data["photo_src"] = tour_photo_src(data.get("photo_url"))
    return data


def can_manage_tour(tour_id):
    # guide owns tour, or admin — used before edit/delete
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour or not current_user.is_authenticated:
        return None
    if current_user.role == "admin":
        return tour
    if current_user.role == "guide" and tour["guide_id"] == current_user.id:
        return tour
    return None


def parse_max_participants(raw_value, default=15):
    # safe int from form — party size and max participants
    try:
        return max(1, int(raw_value))
    except (TypeError, ValueError):
        return default


def edit_tour_context(tour_id, tour_row, use_form=False):
    # bundle tour + photos + languages for edit_tour.html (also on validation error)
    tour_data = dict(tour_row)
    if use_form:
        tour_data.update({
            "title": request.form.get("txt_title", tour_data.get("title", "")),
            "schedule": request.form.get("txt_schedule", tour_data.get("schedule", "")),
            "duration": request.form.get("txt_duration", tour_data.get("duration", "")),
            "payment": request.form.get("txt_payment", tour_data.get("payment", "")),
            "summary": request.form.get("txt_summary", tour_data.get("summary", "")),
            "meeting_point": request.form.get("txt_meeting_point", tour_data.get("meeting_point", "")),
            "meeting_map_link": request.form.get("txt_meeting_map_link", tour_data.get("meeting_map_link", "")),
            "max_participants": parse_max_participants(request.form.get("txt_max_participants"), tour_data.get("max_participants") or 15),
            "languages_list": request.form.getlist("txt_languages"),
            "stops_list": parse_stops_from_form(),
        })
    else:
        tour_data["languages_list"] = tours_dao.get_languages_for_tour(tour_id)
        tour_data["stops_list"] = [
            {"name": s["name"], "description": s["description"]}
            for s in tour_stops_dao.get_stops_for_tour(tour_id)
        ]
    return {
        "tour": tour_data,
        "photos": [dict(p) for p in tour_photos_dao.get_photos_for_tour(tour_id)],
        "max_photos": tour_photos_dao.MAX_PHOTOS_PER_TOUR,
        "available_languages": AVAILABLE_LANGUAGES,
        "min_stops": tour_stops_dao.MIN_STOPS_PER_TOUR,
        "max_stops": tour_stops_dao.MAX_STOPS_PER_TOUR,
    }


def new_tour_form_data():
    # keep form values when validation fails on create tour
    return {
        "title": request.form.get("txt_title", ""),
        "schedule": request.form.get("txt_schedule", ""),
        "duration": request.form.get("txt_duration", ""),
        "payment": request.form.get("txt_payment", "Free Tour"),
        "summary": request.form.get("txt_summary", ""),
        "meeting_point": request.form.get("txt_meeting_point", ""),
        "meeting_map_link": request.form.get("txt_meeting_map_link", ""),
        "max_participants": parse_max_participants(request.form.get("txt_max_participants")),
        "languages_list": request.form.getlist("txt_languages"),
        "stops": parse_stops_from_form(),
    }


def filter_languages(selected):
    # only allow languages from our fixed list
    return [lang for lang in selected if lang in AVAILABLE_LANGUAGES]

def parse_stops_from_form():
    # form sends txt_stop_name_1, txt_stop_desc_1, ... guides can add more via js
    stops = []
    for i in range(1, tour_stops_dao.MAX_STOPS_PER_TOUR + 1):
        name = request.form.get(f"txt_stop_name_{i}", "").strip()
        if name:
            description = request.form.get(f"txt_stop_desc_{i}", "").strip()
            stops.append({"name": name, "description": description})
    return stops

# --- public pages ---

@app.route("/")
def home():
    # landing page with featured tour cards
    tours = [tour_dict(row) for row in tours_dao.get_tours()]
    return render_template("home.html", tours=tours)


@app.route("/tours")
def tours():
    # full tour list with optional language filter
    selected_language = request.args.get("language", "")
    if selected_language and selected_language not in AVAILABLE_LANGUAGES:
        selected_language = ""
    if selected_language:
        rows = tours_dao.get_tours_by_language(selected_language)
    else:
        rows = tours_dao.get_tours()
    return render_template(
        "tour.html",
        tours=[tour_dict(row) for row in rows],
        available_languages=AVAILABLE_LANGUAGES,
        selected_language=selected_language,
        page_error=request.args.get("error", ""),
    )


@app.route("/tour/<int:tour_id>")
def tour_detail(tour_id):
    # single tour page — photos, details, booking form
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404
    tour_data = dict(tour)
    langs = tours_dao.get_languages_for_tour(tour_id)
    tour_data["languages"] = ", ".join(langs) if langs else "Not set"
    photos = [dict(p) for p in tour_photos_dao.get_photos_for_tour(tour_id)]
    stops = [dict(s) for s in tour_stops_dao.get_stops_for_tour(tour_id)]
    tour_data["photo_src"] = tour_photo_src(photos[0]["photo_path"] if photos else tour_data.get("photo_url"))
    return render_template(
        "tour_detail.html",
        tour=tour_data,
        photos=photos,
        stops=stops,
        booking_error=request.args.get("booking_error", ""),
    )


@app.route("/contact")
def contact():
    # static contact info page
    return render_template("contact.html")


# --- auth ---

@app.route("/signup")
def signup():
    # show register form
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    # new accounts are always participants (exam rule)
    email = request.form.get("txt_email")
    if users_dao.get_user_by_email(email):
        return render_template("register.html", form_error="Email already registered. Try logging in instead.")
    users_dao.new_user(
        request.form.get("txt_name"),
        request.form.get("txt_surname"),
        email,
        request.form.get("txt_password"),
        "participant",  # only participants can self-register
    )
    return redirect(url_for("home"))


@app.route("/login")
def login():
    # show login form
    return render_template("login.html")


@app.route("/do_login", methods=["POST"])
def do_login():
    # check email/password then start flask-login session
    user = users_dao.get_user_by_email(request.form.get("txt_email"))
    if not user or user["password"] != request.form.get("txt_password"):
        return render_template("login.html", error="Invalid email or password")
    login_user(User(user))
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    # end session
    logout_user()
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # preview only — no real email sent; checks email exists in db
    if request.method == "POST":
        email = request.form.get("txt_email", "").strip()
        if not email:
            return render_template("forgot_password.html", error="Please enter your email.", email=email)
        user = users_dao.get_user_by_email(email)
        if not user:
            return render_template(
                "forgot_password.html",
                error="No account found with that email.",
                email=email,
            )
        return render_template("forgot_password.html", success=True, email=email)
    return render_template("forgot_password.html")

@app.route("/profile/password", methods=["GET", "POST"])
def change_password():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    if request.method == "POST":
        current = request.form.get("txt_current_password", "")
        new_pass = request.form.get("txt_new_password", "")
        confirm = request.form.get("txt_confirm_password", "")

        if current != current_user.password:
            return render_template(
                "change_password.html",
                form_error="Current password is wrong.",
            )

        if not new_pass:
            return render_template(
                "change_password.html",
                form_error="New password is required.",
            )

        if new_pass != confirm:
            return render_template(
                "change_password.html",
                form_error="New passwords do not match.",
            )

        users_dao.update_password(current_user.id, new_pass)
        return redirect(url_for("profile"))

    return render_template("change_password.html")



@app.route("/profile")
def profile():
    # logged-in user info
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return render_template("profile.html", user=current_user)

@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("txt_name", "").strip()
        surname = request.form.get("txt_surname", "").strip()

        if not name or not surname:
            return render_template(
                "edit_profile.html",
                user=current_user,
                form_error="Name and surname are required.",
            )

        users_dao.update_profile(current_user.id, name, surname)
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=current_user)


@app.route("/dashboard")
def dashboard():
    # send each role to the right page
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if current_user.role == "participant":
        return redirect(url_for("my_bookings"))
    if current_user.role == "guide":
        return redirect(url_for("guide_bookings"))
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("home"))


# --- guide: create / edit / delete tours ---

@app.route("/guide/new-tour", methods=["GET", "POST"])
def new_tour():
    # guide creates a tour with photos and languages
    if not current_user.is_authenticated or current_user.role != "guide":
        return redirect(url_for("home"))
    if request.method == "POST":
        selected_languages = filter_languages(request.form.getlist("txt_languages"))
        if not selected_languages:
            return render_template(
                "new_tour.html",
                available_languages=AVAILABLE_LANGUAGES,
                form_error="Select at least one language.",
                form=new_tour_form_data(),
                min_stops=tour_stops_dao.MIN_STOPS_PER_TOUR,
                max_stops=tour_stops_dao.MAX_STOPS_PER_TOUR,
            )
        stops = parse_stops_from_form()
        if len(stops) < tour_stops_dao.MIN_STOPS_PER_TOUR:
            return render_template(
                "new_tour.html",
                available_languages=AVAILABLE_LANGUAGES,
                form_error=f"Add at least {tour_stops_dao.MIN_STOPS_PER_TOUR} tour stops.",
                form=new_tour_form_data(),
                min_stops=tour_stops_dao.MIN_STOPS_PER_TOUR,
                max_stops=tour_stops_dao.MAX_STOPS_PER_TOUR,
            )
        max_participants = parse_max_participants(request.form.get("txt_max_participants"))
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
            current_user.id,
        )
        save_uploaded_photos(tour_id, request.files.getlist("txt_photos"))
        sync_tour_cover_photo(tour_id)
        tours_dao.set_tour_languages(tour_id, selected_languages)
        tour_stops_dao.set_tour_stops(tour_id, stops)
        return redirect(url_for("tours"))
    return render_template(
        "new_tour.html",
        available_languages=AVAILABLE_LANGUAGES,
        form={},
        min_stops=tour_stops_dao.MIN_STOPS_PER_TOUR,
        max_stops=tour_stops_dao.MAX_STOPS_PER_TOUR,
    )


@app.route("/guide/edit-tour/<int:tour_id>", methods=["GET", "POST"])
def edit_tour(tour_id):
    # update tour — locked for guides once someone booked
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))
    # guides locked after first booking — admin can still edit
    if current_user.role != "admin" and bookings_dao.tour_has_bookings(tour_id):
        return redirect(url_for("tours", error="This tour already has bookings and cannot be edited."))
    if request.method == "POST":
        selected_languages = filter_languages(request.form.getlist("txt_languages"))
        if not selected_languages:
            ctx = edit_tour_context(tour_id, tour, use_form=True)
            ctx["form_error"] = "Select at least one language."
            return render_template("edit_tour.html", **ctx)
        stops = parse_stops_from_form()
        if len(stops) < tour_stops_dao.MIN_STOPS_PER_TOUR:
            ctx = edit_tour_context(tour_id, tour, use_form=True)
            ctx["form_error"] = f"Add at least {tour_stops_dao.MIN_STOPS_PER_TOUR} tour stops."
            return render_template("edit_tour.html", **ctx)
        max_participants = parse_max_participants(request.form.get("txt_max_participants"))
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
        tour_stops_dao.set_tour_stops(tour_id, stops)
        return redirect(url_for("tours"))
    ctx = edit_tour_context(tour_id, tour, use_form=False)
    ctx["form_error"] = request.args.get("error", "")
    return render_template("edit_tour.html", **ctx)


@app.route("/guide/delete-tour/<int:tour_id>", methods=["POST"])
def delete_tour_route(tour_id):
    # remove tour, photos on disk, and related db rows
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))
    if current_user.role != "admin" and bookings_dao.tour_has_bookings(tour_id):
        return redirect(url_for("tours", error="This tour already has bookings and cannot be deleted."))
    for photo in tour_photos_dao.get_photos_for_tour(tour_id):
        remove_photo_file(photo["photo_path"])
    remove_photo_file(dict(tour).get("photo_url"))
    tours_dao.delete_tour(tour_id)
    return redirect(url_for("tours"))


@app.route("/guide/tour-photo/<int:photo_id>/delete", methods=["POST"])
def delete_tour_photo(photo_id):
    # delete one gallery image from edit page
    if not current_user.is_authenticated or current_user.role not in ("guide", "admin"):
        return redirect(url_for("home"))
    photo = tour_photos_dao.get_photo_by_id(photo_id)
    if not photo:
        return redirect(url_for("tours"))
    tour = can_manage_tour(photo["tour_id"])
    if not tour:
        return redirect(url_for("tours"))
    if current_user.role != "admin" and bookings_dao.tour_has_bookings(photo["tour_id"]):
        return redirect(url_for("edit_tour", tour_id=photo["tour_id"], error="This tour already has bookings and cannot be edited."))
    remove_photo_file(photo["photo_path"])
    tour_photos_dao.delete_photo(photo_id)
    sync_tour_cover_photo(photo["tour_id"])
    return redirect(url_for("edit_tour", tour_id=photo["tour_id"]))


@app.route("/guide/bookings")
def guide_bookings():
    # guide sees who booked their tours
    if not current_user.is_authenticated or current_user.role != "guide":
        return redirect(url_for("home"))
    bookings = [dict(r) for r in bookings_dao.get_bookings_by_guide(current_user.id)]
    return render_template("guide_bookings.html", bookings=bookings)


# --- participant bookings ---

@app.route("/tour/<int:tour_id>/book", methods=["POST"])
def book_tour(tour_id):
    # participant books a date — checks capacity first
    if not current_user.is_authenticated or current_user.role != "participant":
        return redirect(url_for("tour_detail", tour_id=tour_id))
    tour_date = request.form.get("txt_tour_date")
    if not tour_date:
        return redirect(url_for("tour_detail", tour_id=tour_id))
    party_size = parse_max_participants(request.form.get("txt_party_size", "1"))
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404
    max_participants = tour["max_participants"] or 15
    remaining = max_participants - bookings_dao.get_booked_spots(tour_id, tour_date)
    if party_size > remaining:
        return redirect(url_for("tour_detail", tour_id=tour_id, booking_error=f"Only {remaining} spot(s) left on that date."))
    announce_email = request.form.get("txt_announce_email", "").strip()
    announce_phone = request.form.get("txt_announce_phone", "").strip()
    if not announce_email and not announce_phone:
        return redirect(url_for(
            "tour_detail", tour_id=tour_id,
            booking_error="Please add an email or phone number for tour announcements.",
        ))
    bookings_dao.create_booking(
        tour_id, current_user.id, tour_date, party_size,
        request.form.get("txt_notes", "").strip(),
        announce_email, announce_phone,
    )
    return redirect(url_for("my_bookings"))


@app.route("/my-bookings")
def my_bookings():
    # participant's own booking list
    if not current_user.is_authenticated or current_user.role != "participant":
        return redirect(url_for("home"))
    bookings = [dict(r) for r in bookings_dao.get_bookings_by_participant(current_user.id)]
    return render_template("my_bookings.html", bookings=bookings)


@app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    # participant cancels their own booking
    if not current_user.is_authenticated or current_user.role != "participant":
        return redirect(url_for("home"))
    bookings_dao.cancel_booking(booking_id, current_user.id)
    return redirect(url_for("my_bookings"))


@app.route("/tour/<int:tour_id>/availability")
def tour_availability(tour_id):
    # json for the booking form — spots left on a date
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return {"error": "Tour not found"}, 404
    tour_date = request.args.get("date", "")
    if not tour_date:
        return {"error": "date required"}, 400
    max_participants = tour["max_participants"] or 15
    booked = bookings_dao.get_booked_spots(tour_id, tour_date)
    return {"max": max_participants, "booked": booked, "remaining": max(0, max_participants - booked)}


# --- admin ---

@app.route("/admin")
def admin_dashboard():
    # stats + tables for guides, participants, bookings
    if not current_user.is_authenticated or current_user.role != "admin":
        return redirect(url_for("home"))
    return render_template(
        "admin.html",
        stats={
            "tours_count": tours_dao.count_tours(),
            "users_count": users_dao.count_users(),
            "guides_count": users_dao.count_by_role("guide"),
            "participants_count": users_dao.count_by_role("participant"),
            "bookings_count": bookings_dao.count_bookings(),
        },
        guides=[dict(u) for u in users_dao.get_users_by_role("guide")],
        participants=[dict(u) for u in users_dao.get_users_by_role("participant")],
        bookings=[dict(b) for b in bookings_dao.get_all_bookings()],
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
