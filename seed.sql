-- sample accounts (the rest of the data - tours, schedules, bookings - is already
-- in silkstep.db). passwords are plain text on purpose, it's just a course project.
INSERT INTO users (name, surname, email, password, role) VALUES
('Ali', 'Guide', 'guide1@test.com', 'pass123', 'guide'),
('Sara', 'Guide', 'guide2@test.com', 'pass123', 'guide'),
('Mo', 'Traveler', 'user1@test.com', 'pass123', 'participant'),
('Anna', 'Traveler', 'user2@test.com', 'pass123', 'participant'),
('Luca', 'Traveler', 'user3@test.com', 'pass123', 'participant'),
('Admin', 'SilkStep', 'admin@test.com', 'admin123', 'admin');
