CREATE TABLE IF NOT EXISTS tour_languages (
    tour_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    PRIMARY KEY (tour_id, language),
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);