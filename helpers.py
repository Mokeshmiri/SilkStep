import os
import uuid
from datetime import datetime

from flask import url_for, request, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

import bookings_dao
import tour_photos_dao
import tours_dao
import users_dao
import tour_stops_dao
import tour_schedule_dao

# small helpers used by the routes in app.py, kept here so app.py stays shorter

AVAILABLE_LANGUAGES = ["Italian", "English", "Spanish", "Portuguese", "German"]
ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# weekday order for the weekly schedule - 0=Mon ... 6=Sun (matches date.weekday())
WEEKDAYS = [
    (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
    (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
]

# buckets for the duration filter on /tours (label, min_minutes, max_minutes)
DURATION_BUCKETS = [
    ("short", "Up to 2 hours", 0, 120),
    ("medium", "2 to 4 hours", 121, 240),
    ("long", "More than 4 hours", 241, 100000),
]


# --- photo helpers ---

def allowed_photo(filename):
    # block weird file types on upload
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS


def save_image(file, prefix):
    # save one uploaded image to static/uploads, return path like uploads/<prefix>_abc.jpg
    if not file or not file.filename or not allowed_photo(file.filename):
        return ""
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique = uuid.uuid4().hex[:8]
    filename = secure_filename(f"{prefix}_{unique}.{ext}")
    upload_dir = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f"uploads/{filename}"


def save_tour_photo(file, tour_id):
    # gallery photo for a tour
    return save_image(file, f"tour_{tour_id}")


def remove_photo_file(photo_path):
    # delete file from disk when removing a gallery photo
    if not photo_path or photo_path.startswith("http"):
        return
    file_path = os.path.join(current_app.root_path, "static", photo_path)
    if os.path.exists(file_path):
        os.remove(file_path)


def save_uploaded_photos(tour_id, files):
    # loop file input - stops at 5 photos per tour
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
        tour["title"], tour["schedule"], tour["duration"], tour["summary"],
        cover, tour["meeting_point"] or "", tour["meeting_map_link"] or "", tour["max_participants"] or 15,
        tour["duration_minutes"],
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
    # guide owns tour, or admin - used before edit/delete
    tour = tours_dao.get_tour_by_id(tour_id)
    if not tour or not current_user.is_authenticated:
        return None
    if current_user.role == "admin":
        return tour
    if current_user.role == "guide" and tour["guide_id"] == current_user.id:
        return tour
    return None


def parse_max_participants(raw_value, default=15):
    # safe int from form - party size and max participants
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
            "summary": request.form.get("txt_summary", tour_data.get("summary", "")),
            "meeting_point": request.form.get("txt_meeting_point", tour_data.get("meeting_point", "")),
            "meeting_map_link": request.form.get("txt_meeting_map_link", tour_data.get("meeting_map_link", "")),
            "max_participants": parse_max_participants(request.form.get("txt_max_participants"), tour_data.get("max_participants") or 15),
            "languages_list": request.form.getlist("txt_languages"),
            "stops_list": parse_stops_from_form(),
        })
        schedule_map = schedule_to_map(parse_schedule_from_form())
        duration_minutes = parse_duration_minutes()
    else:
        tour_data["languages_list"] = tours_dao.get_languages_for_tour(tour_id)
        tour_data["stops_list"] = [
            {"name": s["name"], "description": s["description"]}
            for s in tour_stops_dao.get_stops_for_tour(tour_id)
        ]
        schedule_map = schedule_to_map([
            {"weekday": s["weekday"], "start_time": s["start_time"]}
            for s in tour_schedule_dao.get_schedule_for_tour(tour_id)
        ])
        duration_minutes = tour_data.get("duration_minutes")
    return {
        "tour": tour_data,
        "photos": [dict(p) for p in tour_photos_dao.get_photos_for_tour(tour_id)],
        "max_photos": tour_photos_dao.MAX_PHOTOS_PER_TOUR,
        "available_languages": tour_language_options(tour_data.get("guide_id")),
        "min_stops": tour_stops_dao.MIN_STOPS_PER_TOUR,
        "max_stops": tour_stops_dao.MAX_STOPS_PER_TOUR,
        "weekdays": WEEKDAYS,
        "schedule_map": schedule_map,
        "duration_minutes": duration_minutes,
    }


def new_tour_form_data():
    # keep form values when validation fails on create tour
    return {
        "title": request.form.get("txt_title", ""),
        "summary": request.form.get("txt_summary", ""),
        "meeting_point": request.form.get("txt_meeting_point", ""),
        "meeting_map_link": request.form.get("txt_meeting_map_link", ""),
        "max_participants": parse_max_participants(request.form.get("txt_max_participants")),
        "languages_list": request.form.getlist("txt_languages"),
        "stops": parse_stops_from_form(),
    }


def filter_languages(selected, allowed=None):
    # keep only languages that are allowed (the fixed 5, or a guide's own languages)
    allowed = allowed if allowed is not None else AVAILABLE_LANGUAGES
    return [lang for lang in selected if lang in allowed]


def tour_language_options(guide_id):
    # a tour's languages must come from the guide's spoken languages
    langs = users_dao.get_user_languages(guide_id) if guide_id else []
    # fallback for old tours with no guide languages set
    return langs or AVAILABLE_LANGUAGES


def booking_start_datetime(tour_id, tour_date):
    # combine the booked date with the tour's start time for that weekday
    try:
        day = datetime.strptime(tour_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
    start_time = tour_schedule_dao.get_start_time(tour_id, day.weekday())
    if not start_time:
        return None
    try:
        hour, minute = (int(part) for part in start_time.split(":"))
    except ValueError:
        hour, minute = 0, 0
    return datetime(day.year, day.month, day.day, hour, minute)


def parse_stops_from_form():
    # form sends txt_stop_name_1, txt_stop_desc_1, ... guides can add more via js
    stops = []
    for i in range(1, tour_stops_dao.MAX_STOPS_PER_TOUR + 1):
        name = request.form.get(f"txt_stop_name_{i}", "").strip()
        if name:
            description = request.form.get(f"txt_stop_desc_{i}", "").strip()
            stops.append({"name": name, "description": description})
    return stops


def parse_schedule_from_form():
    # form sends a checkbox txt_day_<idx> + a time txt_time_<idx> for each weekday
    schedule = []
    for idx, _name in WEEKDAYS:
        if request.form.get(f"txt_day_{idx}"):
            start_time = request.form.get(f"txt_time_{idx}", "").strip()
            if start_time:
                schedule.append({"weekday": idx, "start_time": start_time})
    return schedule


def schedule_to_map(schedule):
    # {weekday_int: "HH:MM"} so the form can pre-check days and fill times
    return {item["weekday"]: item["start_time"] for item in schedule}


def schedule_display(schedule):
    # short text like "Sat 10:00, Sun 14:00" for the legacy schedule column / cards
    names = dict(WEEKDAYS)
    ordered = sorted(schedule, key=lambda item: item["weekday"])
    return ", ".join(f"{names[item['weekday']][:3]} {item['start_time']}" for item in ordered)


def parse_duration_minutes():
    # structured duration in minutes; None when the form value is missing/invalid
    try:
        return max(15, int(request.form.get("txt_duration_minutes", "")))
    except (TypeError, ValueError):
        return None


def parse_booking_guests(party_size):
    # party_size includes the logged-in participant, so guests are party_size - 1
    guests = []
    extra_count = max(0, party_size - 1)

    for i in range(1, extra_count + 1):
        first_name = request.form.get(f"txt_guest_first_{i}", "").strip()
        last_name = request.form.get(f"txt_guest_last_{i}", "").strip()

        if not first_name or not last_name:
            return None

        guests.append({
            "first_name": first_name,
            "last_name": last_name,
        })

    return guests
