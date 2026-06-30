-- silkstep database schema
-- this is the full structure of silkstep.db (the db file is already in the repo,
-- this file is just here as a reference / to rebuild from scratch if needed)

-- users: guides, participants and one admin
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('guide', 'participant', 'admin'))
);

-- tours: each one belongs to a guide
-- schedule/duration are old display-text columns kept for back compat;
-- duration_minutes + the tour_schedule table hold the real structured data
CREATE TABLE tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    schedule TEXT NOT NULL,
    duration TEXT NOT NULL,
    summary TEXT NOT NULL,
    guide_id INTEGER,
    meeting_point TEXT,
    max_participants INTEGER DEFAULT 15,
    photo_url TEXT,
    meeting_map_link TEXT,
    duration_minutes INTEGER
);

-- which languages a tour is offered in
CREATE TABLE tour_languages (
    tour_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    PRIMARY KEY (tour_id, language),
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

-- languages a guide speaks (a tour's languages must be a subset of these)
CREATE TABLE user_languages (
    user_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    PRIMARY KEY (user_id, language),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- weekly schedule: one start time per weekday (0=mon ... 6=sun)
CREATE TABLE tour_schedule (
    tour_id INTEGER NOT NULL,
    weekday INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    PRIMARY KEY (tour_id, weekday),
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

-- stops along the route (at least 4 per tour)
CREATE TABLE tour_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

-- promotional photos (up to 5 per tour)
CREATE TABLE tour_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    photo_path TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

-- reservations: one row = one booking for a date (1 to 4 people)
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    tour_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    party_size INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    announce_email TEXT,
    announce_phone TEXT,
    FOREIGN KEY (tour_id) REFERENCES tours(id),
    FOREIGN KEY (participant_id) REFERENCES users(id)
);

-- extra people on a booking (the up-to-3 added names)
CREATE TABLE booking_guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- post-tour report: for a past date the guide says how many really came + one photo
CREATE TABLE tour_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    tour_date TEXT NOT NULL,
    attended_count INTEGER NOT NULL,
    photo_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tour_id, tour_date),
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);
