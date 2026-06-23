CREATE TABLE tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    schedule TEXT NOT NULL,
    duration TEXT NOT NULL,
    payment TEXT NOT NULL,
    summary TEXT NOT NULL
);

INSERT INTO tours (title, schedule, duration, payment, summary) VALUES
('Old Tehran Walking Tour', 'Sat & Sun at 10:00 AM', '4 hours', 'Free Tour',
 'Explore the historic heart of Tehran, from the 16th-century Shahreza Palace to the 13th-century Jameh Mosque.'),
('Bazaar & Market Tour', 'Mon, Wed, Fri at 2:00 PM', '3 hours', 'Paid Tour',
 'Discover the vibrant markets of Tehran, from the Grand Bazaar to the spice and textile souks.'),
('Museum & Art Tour', 'Tue & Thu at 3:00 PM', '2 hours', 'Paid Tour',
 'Visit the National Museum of Iran and explore the city''s vibrant art scene.'),
('Private Walking Tour', 'to be defined', 'Max 12 hours', 'Exclusive Tour',
 'Customized walking tour for groups or individuals, tailored to your interests and schedule.');