# silkstep

course: 01VRP intro web apps (2025/2026)  
student: mo mokashmiri - s308968

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

**target device: desktop** (designed for desktop browsers; layout still works smaller thanks to bootstrap, but desktop is the target).

---

## run locally

```bash
pip install -r requirements.txt
python3 app.py
```

open: http://127.0.0.1:5001

(db is already in the repo - no extra setup needed on my machine)

---

## test accounts

see `credentials.txt` for full list. quick ones:

| role | email | password |
|------|-------|----------|
| guide | guide1@test.com | pass123 |
| participant | user1@test.com | pass123 |
| admin | admin@test.com | admin123 |

you can register as a **participant** or a **guide** (guides also pick the languages they speak, and can change them later from their profile). the **admin** account is seed-only.

---

## main features (exam requirements)

- two user types: guides + participants (guide cant book, participant cant create)
- a guide keeps the languages they speak on their profile (set at registration,
  editable later); when they create a tour they only see those languages to pick from
- tours with: title, weekly schedule (day + start time), meeting point, duration
  in minutes, language(s), max participants, 4+ stops, description, up to 5 photos
- home + tours list, filter by **date / duration / language**
- tour detail + booking: pick a date from the weekly schedule, 1-4 people
  (add up to 3 names), capacity check per date, email/phone for announcements
- cancel only allowed up to 24h before the start time
- participant profile (my bookings): date, start time, meeting point, people, names
- guide profile: reservations grouped per date with total expected people
- post-tour report: for past dates with bookings, declare attendance + 1 photo
- each tour poster also shows which guide posted it
- guide: create/edit/delete tours (locked after the first booking)
- admin: a simple monitoring page for myself - counts + guides (with languages) +
  participants + all bookings. admin still has full access (can edit/delete any tour).
  it's not part of the exam minimum, i just made it to watch the site
- contact page + editable profile + change password + navbar dropdown

---

## extra features (beyond minimum)

stuff on the site that makes it feel more like a real product, not just the bare exam checklist:

**homepage highlights** (three boxes under the hero banner):

| box | what it means |
|-----|----------------|
| free to join | tours can be free - no paywall to browse or book |
| local guides | tours are run by tehran guides, not a generic catalog |
| tehran heritage routes | themed walks around historic tehran / silk road vibe |

**ui polish**

- hero banner with gradient + tagline (*every step tells a story*)
- square tour cards (`aspect-ratio 1:1`) so the grid looks even
- photo gallery modal with prev/next arrows + keyboard (left/right keys)
- live spots-left on booking form (calls `/tour/<id>/availability` when you pick a date)
- navbar name dropdown (profile, dashboard, logout)
- form validation errors stay on the same page (not a blank 400)
- tour stops (4+ per route) on create/edit + tour detail page
- editable profile, forgot password, booking contact email/phone

**brand name**

- shown as **silk step** (two words) on the home hero - reads easier than one glued word

---

## deploy (pythonanywhere)

1. upload the project folder (or push to github and clone it on pythonanywhere).
2. make a virtualenv and `pip install -r requirements.txt`.
3. add a new web app -> manual config -> flask, point it at the venv.
4. edit the wsgi file so it imports the app, e.g.:

```python
import sys
path = "/home/<username>/SilkStep"
if path not in sys.path:
    sys.path.append(path)
from app import app as application
```

5. set the static files mapping: url `/static/` -> `/home/<username>/SilkStep/static`.
6. make sure `silkstep.db` is uploaded too (it already has the sample data).
7. reload the web app.

**live site:** https://mokeshmiri.pythonanywhere.com

---

## project structure (short)

```
app.py              routes + flask-login
helpers.py          small helper functions (photos, schedule, parsing) - keeps app.py short
*_dao.py            database stuff (one file per table-ish)
user_model.py       user class for flask-login
templates/          html pages
static/css/         custom styles
static/uploads/     tour photos
schema.sql          full db structure (reference)
seed.sql            sample accounts
silkstep.db         the actual sqlite db (already filled)
credentials.txt     exam test logins
```
