# silkstep

course: 01VRP intro web apps (2025/2026)  
student: mo mokashmiri — s308968

free walking tours in tehran. tagline: *every step tells a story.*

---

## what it is

small flask app for booking walking tours. one city (tehran), many tours. guides create tours, people book a date, admin can see stats.

inspired by stuff like persian walk / freetour but built for the exam project.

---

## tech

- python + flask
- sqlite (`silkstep.db`)
- flask-login (sessions / roles)
- bootstrap 5
- html templates + a bit of css/js

---

## run locally

```bash
pip install -r requirements.txt
python3 app.py
```

open: http://127.0.0.1:5001

(db is already in the repo — no extra setup needed on my machine)

---

## test accounts

see `credentials.txt` for full list. quick ones:

| role | email | password |
|------|-------|----------|
| guide | guide1@test.com | pass123 |
| participant | user1@test.com | pass123 |
| admin | admin@test.com | admin123 |

register only makes **participant** accounts. guides/admin are seed data.

---

## main features (exam requirements)

- home + tours list (filter by language)
- tour detail + book with date, party size, notes
- capacity check — cant overbook a date
- up to 5 photos per tour, click to enlarge
- guide: create/edit/delete tours (locked after first booking)
- admin: dashboard with users + bookings tables, can still edit locked tours
- my bookings / guide bookings / cancel booking
- contact page + profile + simple navbar dropdown

---

## extra features (beyond minimum)

stuff on the site that makes it feel more like a real product, not just the bare exam checklist:

**homepage highlights** (three boxes under the hero banner):

| box | what it means |
|-----|----------------|
| free to join | tours can be free — no paywall to browse or book |
| local guides | tours are run by tehran guides, not a generic catalog |
| tehran heritage routes | themed walks around historic tehran / silk road vibe |

**ui polish**

- hero banner with gradient + tagline (*every step tells a story*)
- square tour cards (`aspect-ratio 1:1`) so the grid looks even
- photo gallery modal with prev/next arrows + keyboard (← →)
- live spots-left on booking form (calls `/tour/<id>/availability` when you pick a date)
- payment badges on cards (free / paid / exclusive)
- navbar name dropdown (profile, dashboard, logout)
- form validation errors stay on the same page (not a blank 400)
- lowercase comments in python + `{# ... #}` in templates for graders

**brand name**

- shown as **silk step** (two words) on the home hero — reads easier than one glued word

---

## still todo

- tour stops (4+ per tour) — not done yet
- deploy on pythonanywhere

---

## project structure (short)

```
app.py              routes + flask-login
*_dao.py            database stuff
user_model.py       user class for flask-login
templates/          html pages
static/css/         custom styles
static/uploads/     tour photos
*.sql               db migrations
credentials.txt     exam test logins
```

---

## notes for oral

- roles: guest (browse), participant (book), guide (own tours), admin (stats)
- booking lock: guide cant edit tour after someone booked; admin can
- photos in `tour_photos` table, files in `static/uploads/`
- capacity = sum of `party_size` for that tour + date vs `max_participants`
