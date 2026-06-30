from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user

import bookings_dao
import tour_photos_dao
import tours_dao
import users_dao
import tour_stops_dao
import tour_schedule_dao
import tour_reports_dao
from user_model import User

# helpers in helpers.py
from helpers import (
    AVAILABLE_LANGUAGES, WEEKDAYS, DURATION_BUCKETS,
    allowed_photo, save_image, save_tour_photo, remove_photo_file,
    save_uploaded_photos, sync_tour_cover_photo, tour_photo_src, tour_dict,
    can_manage_tour, parse_max_participants, edit_tour_context, new_tour_form_data,
    filter_languages, tour_language_options, booking_start_datetime,
    parse_stops_from_form, parse_schedule_from_form, schedule_to_map,
    schedule_display, parse_duration_minutes, parse_booking_guests,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"

# flask login setup - loads user from db on each request
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    # reload user from db when flask login reads the session cookie
    row = users_dao.get_user_by_id(int(user_id))
    return User(row) if row else None


# --- public pages ---

@app.route("/")
def home():
    tours = [tour_dict(row) for row in tours_dao.get_tours()]
    return render_template("home.html", tours=tours)


@app.route("/tours")
def tours():
    # full tour list with optional language / date / duration filters
    selected_language = request.args.get("language", "")
    selected_date = request.args.get("date", "")
    selected_duration = request.args.get("duration", "")
    if selected_language and selected_language not in AVAILABLE_LANGUAGES:
        selected_language = ""

    if selected_language:
        rows = tours_dao.get_tours_by_language(selected_language)
    else:
        rows = tours_dao.get_tours()
    tour_list = [tour_dict(row) for row in rows]

# filter by weekday of chosen date
    if selected_date:
        try:
            weekday = datetime.strptime(selected_date, "%Y-%m-%d").weekday()
            available_ids = tour_schedule_dao.get_tour_ids_for_weekday(weekday)
            tour_list = [t for t in tour_list if t["id"] in available_ids]
        except ValueError:
            selected_date = ""

# filter by duration
    bucket = next((b for b in DURATION_BUCKETS if b[0] == selected_duration), None)
    if bucket:
        _key, _label, low, high = bucket
        tour_list = [
            t for t in tour_list
            if t.get("duration_minutes") is not None and low <= t["duration_minutes"] <= high
        ]
    else:
        selected_duration = ""

    return render_template(
        "tour.html",
        tours=tour_list,
        available_languages=AVAILABLE_LANGUAGES,
        selected_language=selected_language,
        selected_date=selected_date,
        selected_duration=selected_duration,
        duration_buckets=[(b[0], b[1]) for b in DURATION_BUCKETS],
        page_error=request.args.get("error", ""),
    )


@app.route("/tour/<int:tour_id>")
def tour_detail(tour_id):
    # single tour page - photos, details, booking form
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404
    tour_data = dict(tour)
    langs = tours_dao.get_languages_for_tour(tour_id)
    tour_data["languages"] = ", ".join(langs) if langs else "Not set"
    guide = users_dao.get_user_by_id(tour_data.get("guide_id")) if tour_data.get("guide_id") else None
    tour_data["guide_name"] = f"{guide['name']} {guide['surname']}" if guide else "SilkStep"
    photos = [dict(p) for p in tour_photos_dao.get_photos_for_tour(tour_id)]
    stops = [dict(s) for s in tour_stops_dao.get_stops_for_tour(tour_id)]
    tour_data["photo_src"] = tour_photo_src(photos[0]["photo_path"] if photos else tour_data.get("photo_url"))
    # schedule for display + date picker
    day_names = dict(WEEKDAYS)
    schedule_rows = tour_schedule_dao.get_schedule_for_tour(tour_id)
    schedule = [
        {"day": day_names[s["weekday"]], "start_time": s["start_time"]}
        for s in schedule_rows
    ]
    schedule_weekdays = [s["weekday"] for s in schedule_rows]
    return render_template(
        "tour_detail.html",
        tour=tour_data,
        photos=photos,
        stops=stops,
        schedule=schedule,
        schedule_weekdays=schedule_weekdays,
        today=date.today().isoformat(),
        booking_error=request.args.get("booking_error", ""),
    )


@app.route("/contact")
def contact():
    return render_template("contact.html")


# --- auth ---

@app.route("/signup")
def signup():
    return render_template("register.html", available_languages=AVAILABLE_LANGUAGES, form={})


@app.route("/register", methods=["POST"])
def register():
    # user picks guide or participant, guides can choose the languages they speak
    name = request.form.get("txt_name", "").strip()
    surname = request.form.get("txt_surname", "").strip()
    email = request.form.get("txt_email", "").strip()
    password = request.form.get("txt_password", "")
    role = request.form.get("txt_role", "participant")
    if role not in ("guide", "participant"):
        role = "participant"
    languages = filter_languages(request.form.getlist("txt_languages"))

    def back(error):
        # re-show the form with an error and keep the typed data
        return render_template(
            "register.html",
            form_error=error,
            available_languages=AVAILABLE_LANGUAGES,
            form={"name": name, "surname": surname, "email": email,
                  "role": role, "languages_list": languages},
        )

    if not name or not surname or not email or not password:
        return back("Please fill in all the fields.")
    if users_dao.get_user_by_email(email):
        return back("Email already registered. Try logging in instead.")
    if role == "guide" and not languages:
        return back("Guides must select at least one spoken language.")

    user_id = users_dao.new_user(name, surname, email, password, role)
    if role == "guide":
        users_dao.set_user_languages(user_id, languages)
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/do_login", methods=["POST"])
def do_login():
    user = users_dao.get_user_by_email(request.form.get("txt_email"))
    if not user or user["password"] != request.form.get("txt_password"):
        return render_template("login.html", error="Invalid email or password")
    login_user(User(user))
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # preview only - no real email sent; checks email exists in db
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
    # logged-in user info (guides also see their spoken languages)
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    languages = users_dao.get_user_languages(current_user.id) if current_user.role == "guide" else []
    return render_template("profile.html", user=current_user, languages=languages)

@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    is_guide = current_user.role == "guide"

    if request.method == "POST":
        name = request.form.get("txt_name", "").strip()
        surname = request.form.get("txt_surname", "").strip()
        languages = filter_languages(request.form.getlist("txt_languages")) if is_guide else []

        def back(error):
            return render_template(
                "edit_profile.html",
                user=current_user,
                available_languages=AVAILABLE_LANGUAGES,
                selected_languages=languages,
                form_error=error,
            )

        if not name or not surname:
            return back("Name and surname are required.")
        if is_guide and not languages:
            return back("Pick at least one language you speak.")

        users_dao.update_profile(current_user.id, name, surname)
        if is_guide:
            users_dao.set_user_languages(current_user.id, languages)
        return redirect(url_for("profile"))

    selected = users_dao.get_user_languages(current_user.id) if is_guide else []
    return render_template(
        "edit_profile.html",
        user=current_user,
        available_languages=AVAILABLE_LANGUAGES,
        selected_languages=selected,
    )


@app.route("/dashboard")
def dashboard():
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

def render_new_tour(form_error=""):
# keep form values on error
    return render_template(
        "new_tour.html",
        available_languages=tour_language_options(current_user.id),
        form_error=form_error,
        form=new_tour_form_data(),
        min_stops=tour_stops_dao.MIN_STOPS_PER_TOUR,
        max_stops=tour_stops_dao.MAX_STOPS_PER_TOUR,
        weekdays=WEEKDAYS,
        schedule_map=schedule_to_map(parse_schedule_from_form()),
        duration_minutes=parse_duration_minutes(),
    )


@app.route("/guide/new-tour", methods=["GET", "POST"])
def new_tour():
    if not current_user.is_authenticated or current_user.role != "guide":
        return redirect(url_for("home"))
    if request.method == "POST":
        allowed_langs = tour_language_options(current_user.id)
        selected_languages = filter_languages(request.form.getlist("txt_languages"), allowed_langs)
        if not selected_languages:
            return render_new_tour("Select at least one language (from the ones you speak).")
        schedule = parse_schedule_from_form()
        if not schedule:
            return render_new_tour("Select at least one day and start time for the schedule.")
        duration_minutes = parse_duration_minutes()
        if duration_minutes is None:
            return render_new_tour("Enter a valid duration in minutes.")
        stops = parse_stops_from_form()
        if len(stops) < tour_stops_dao.MIN_STOPS_PER_TOUR:
            return render_new_tour(f"Add at least {tour_stops_dao.MIN_STOPS_PER_TOUR} tour stops.")
        max_participants = parse_max_participants(request.form.get("txt_max_participants"))
        tour_id = tours_dao.create_tour(
            request.form.get("txt_title"),
            schedule_display(schedule),
            f"{duration_minutes} minutes",
            request.form.get("txt_summary"),
            "",
            request.form.get("txt_meeting_point", "").strip(),
            request.form.get("txt_meeting_map_link", "").strip(),
            max_participants,
            current_user.id,
            duration_minutes,
        )
        save_uploaded_photos(tour_id, request.files.getlist("txt_photos"))
        sync_tour_cover_photo(tour_id)
        tours_dao.set_tour_languages(tour_id, selected_languages)
        tour_schedule_dao.set_tour_schedule(tour_id, schedule)
        tour_stops_dao.set_tour_stops(tour_id, stops)
        return redirect(url_for("tours"))
    return render_new_tour()


@app.route("/guide/edit-tour/<int:tour_id>", methods=["GET", "POST"])
def edit_tour(tour_id):
    # update tour - locked for guides once someone booked
    tour = can_manage_tour(tour_id)
    if not tour:
        return redirect(url_for("tours"))
    # guides locked after first booking - admin can still edit
    if current_user.role != "admin" and bookings_dao.tour_has_bookings(tour_id):
        return redirect(url_for("tours", error="This tour already has bookings and cannot be edited."))
    if request.method == "POST":
        allowed_langs = tour_language_options(tour["guide_id"])
        selected_languages = filter_languages(request.form.getlist("txt_languages"), allowed_langs)
        if not selected_languages:
            ctx = edit_tour_context(tour_id, tour, use_form=True)
            ctx["form_error"] = "Select at least one language (from the ones the guide speaks)."
            return render_template("edit_tour.html", **ctx)
        schedule = parse_schedule_from_form()
        if not schedule:
            ctx = edit_tour_context(tour_id, tour, use_form=True)
            ctx["form_error"] = "Select at least one day and start time for the schedule."
            return render_template("edit_tour.html", **ctx)
        duration_minutes = parse_duration_minutes()
        if duration_minutes is None:
            ctx = edit_tour_context(tour_id, tour, use_form=True)
            ctx["form_error"] = "Enter a valid duration in minutes."
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
            schedule_display(schedule),
            f"{duration_minutes} minutes",
            request.form.get("txt_summary"),
            tour["photo_url"] or "",
            request.form.get("txt_meeting_point", "").strip(),
            request.form.get("txt_meeting_map_link", "").strip(),
            max_participants,
            duration_minutes,
        )
        save_uploaded_photos(tour_id, request.files.getlist("txt_photos"))
        sync_tour_cover_photo(tour_id)
        tours_dao.set_tour_languages(tour_id, selected_languages)
        tour_schedule_dao.set_tour_schedule(tour_id, schedule)
        tour_stops_dao.set_tour_stops(tour_id, stops)
        return redirect(url_for("tours"))
    ctx = edit_tour_context(tour_id, tour, use_form=False)
    ctx["form_error"] = request.args.get("error", "")
    return render_template("edit_tour.html", **ctx)


@app.route("/guide/delete-tour/<int:tour_id>", methods=["POST"])
def delete_tour_route(tour_id):
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
    # guide sees reservations grouped by tour + date, with totals and post-tour reports
    if not current_user.is_authenticated or current_user.role != "guide":
        return redirect(url_for("home"))
    now = datetime.now()
    rows = [dict(r) for r in bookings_dao.get_bookings_by_guide(current_user.id)]
    groups = {}
    for b in rows:
        b["guests"] = [dict(g) for g in bookings_dao.get_guests_for_booking(b["id"])]
        key = (b["tour_id"], b["tour_date"])
        if key not in groups:
            start_dt = booking_start_datetime(b["tour_id"], b["tour_date"])
            groups[key] = {
                "tour_id": b["tour_id"],
                "tour_title": b["tour_title"],
                "tour_date": b["tour_date"],
                "start_time": start_dt.strftime("%H:%M") if start_dt else "",
                "is_past": bool(start_dt and start_dt < now),
                "total_people": 0,
                "bookings": [],
                "report": None,
            }
        groups[key]["bookings"].append(b)
        groups[key]["total_people"] += b["party_size"] or 1

    group_list = sorted(groups.values(), key=lambda g: g["tour_date"], reverse=True)
    for group in group_list:
        if group["is_past"]:
            report = tour_reports_dao.get_report(group["tour_id"], group["tour_date"])
            group["report"] = dict(report) if report else None

    return render_template(
        "guide_bookings.html",
        groups=group_list,
        page_error=request.args.get("error", ""),
    )


@app.route("/guide/report", methods=["POST"])
def submit_report():
    # guide declares how many really attended + uploads one evidence photo (past dates only)
    if not current_user.is_authenticated or current_user.role != "guide":
        return redirect(url_for("home"))
    try:
        tour_id = int(request.form.get("tour_id"))
    except (TypeError, ValueError):
        return redirect(url_for("guide_bookings"))
    tour_date = request.form.get("tour_date", "")
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour or tour["guide_id"] != current_user.id:
        return redirect(url_for("guide_bookings"))
    start_dt = booking_start_datetime(tour_id, tour_date)
    if not start_dt or start_dt > datetime.now():
        return redirect(url_for("guide_bookings", error="You can only report a tour date that already took place."))
    if bookings_dao.get_booked_spots(tour_id, tour_date) == 0:
        return redirect(url_for("guide_bookings", error="There are no reservations on that date to report."))
    try:
        attended = max(0, int(request.form.get("txt_attended", "")))
    except (TypeError, ValueError):
        return redirect(url_for("guide_bookings", error="Enter a valid number of attendees."))
    photo_path = save_image(request.files.get("txt_evidence"), f"report_{tour_id}") or None
    tour_reports_dao.save_report(tour_id, tour_date, attended, photo_path)
    return redirect(url_for("guide_bookings"))


# --- participant bookings ---

@app.route("/tour/<int:tour_id>/book", methods=["POST"])
def book_tour(tour_id):
    # participant books a date - checks capacity first
    if not current_user.is_authenticated or current_user.role != "participant":
        return redirect(url_for("tour_detail", tour_id=tour_id))
    tour_date = request.form.get("txt_tour_date")
    if not tour_date:
        return redirect(url_for("tour_detail", tour_id=tour_id))
    party_size = parse_max_participants(request.form.get("txt_party_size", "1"))
    if party_size > 4:
        return redirect(url_for(
            "tour_detail", tour_id=tour_id,
            booking_error="You can only book up to 4 people per tour.",
        ))
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour:
        return "Tour not found", 404
    # date must be valid, not in the past, and a day this tour actually runs
    try:
        booking_day = datetime.strptime(tour_date, "%Y-%m-%d").date()
    except ValueError:
        return redirect(url_for("tour_detail", tour_id=tour_id, booking_error="Please choose a valid date."))
    if booking_day < date.today():
        return redirect(url_for("tour_detail", tour_id=tour_id, booking_error="You cannot book a date in the past."))
    if tour_schedule_dao.get_start_time(tour_id, booking_day.weekday()) is None:
        return redirect(url_for(
            "tour_detail", tour_id=tour_id,
            booking_error="This tour does not run on that day. Check the weekly schedule.",
        ))
    max_participants = tour["max_participants"] or 15
    remaining = max_participants - bookings_dao.get_booked_spots(tour_id, tour_date)
    if party_size > remaining:
        return redirect(url_for("tour_detail", tour_id=tour_id, booking_error=f"Only {remaining} spot(s) left on that date."))
    guests = parse_booking_guests(party_size)
    if guests is None:
        return redirect(url_for(
            "tour_detail", tour_id=tour_id,
            booking_error="Please add first and last name for each extra participant.",
        ))
    announce_email = request.form.get("txt_announce_email", "").strip()
    announce_phone = request.form.get("txt_announce_phone", "").strip()
    if not announce_email and not announce_phone:
        return redirect(url_for(
            "tour_detail", tour_id=tour_id,
            booking_error="Please add an email or phone number for tour announcements.",
        ))
    booking_id = bookings_dao.create_booking(
        tour_id, current_user.id, tour_date, party_size,
        request.form.get("txt_notes", "").strip(),
        announce_email, announce_phone,
    )
    bookings_dao.add_booking_guests(booking_id, guests)
    return redirect(url_for("my_bookings"))


@app.route("/my-bookings")
def my_bookings():
    # participant's own booking list, with start time + meeting point + cancel window
    if not current_user.is_authenticated or current_user.role != "participant":
        return redirect(url_for("home"))
    now = datetime.now()
    bookings = [dict(r) for r in bookings_dao.get_bookings_by_participant(current_user.id)]
    for booking in bookings:
        booking["guests"] = [
            dict(g) for g in bookings_dao.get_guests_for_booking(booking["id"])
        ]
        start_dt = booking_start_datetime(booking["tour_id"], booking["tour_date"])
        booking["start_time"] = start_dt.strftime("%H:%M") if start_dt else ""
        # can still cancel only if the start is more than 24h away
        booking["can_cancel"] = bool(start_dt and start_dt - now >= timedelta(hours=24))
    return render_template(
        "my_bookings.html",
        bookings=bookings,
        page_error=request.args.get("error", ""),
    )


@app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    # participant cancels their own booking, but only up to 24h before the start time
    if not current_user.is_authenticated or current_user.role != "participant":
        return redirect(url_for("home"))
    booking = bookings_dao.get_booking_by_id(booking_id)
    if not booking or booking["participant_id"] != current_user.id:
        return redirect(url_for("my_bookings"))
    start_dt = booking_start_datetime(booking["tour_id"], booking["tour_date"])
    if start_dt and start_dt - datetime.now() < timedelta(hours=24):
        return redirect(url_for(
            "my_bookings",
            error="You can only cancel at least 24 hours before the tour start time.",
        ))
    bookings_dao.cancel_booking(booking_id, current_user.id)
    return redirect(url_for("my_bookings"))


@app.route("/tour/<int:tour_id>/availability")
def tour_availability(tour_id):
    # json for the booking form - spots left on a date
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
    # admin page stats
    if not current_user.is_authenticated or current_user.role != "admin":
        return redirect(url_for("home"))
    guides = [dict(u) for u in users_dao.get_users_by_role("guide")]
    for guide in guides:
        guide["languages"] = users_dao.get_user_languages(guide["id"])
    return render_template(
        "admin.html",
        stats={
            "tours_count": tours_dao.count_tours(),
            "guides_count": users_dao.count_by_role("guide"),
            "participants_count": users_dao.count_by_role("participant"),
            "bookings_count": bookings_dao.count_bookings(),
        },
        guides=guides,
        participants=[dict(u) for u in users_dao.get_users_by_role("participant")],
        bookings=[dict(b) for b in bookings_dao.get_all_bookings()],
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
