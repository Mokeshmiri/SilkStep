# silkstep

course: Introduction to Web Applications (2025/2026)  
student: Mohammad Keshmiri - s308968

free walking tours in tehran. tagline: *every step tells a story.*

---

## what it is

small flask app for booking free walking tours in tehran. guides create tours, participants book dates, and admin can check the platform activity.

inspired by free walking tour websites, but made for this exam project and focused on tehran.

---

## tech

- python + flask
- sqlite (`silkstep.db`)
- flask-login (sessions / roles)
- bootstrap 5
- html templates + a bit of css/js

note: this is an exam/demo project. flask-login is used for sessions.

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

## main features according to project's requirements

- two user types: guides + participants (guides cannot book tours, participants cannot create tours)
- a guide keeps the languages they speak on their profile (set at registration,
  editable later); when they create a tour they only see those languages to pick from
- tours with: title, weekly schedule (day + start time), meeting point, duration
  in minutes, language(s), max participants, 4+ stops, description, and 5 promotional photos
- home + tours list, filter by **date / duration / language**
- tour detail + booking: pick a date from the weekly schedule, 1-4 people
  (add up to 3 names), capacity check per date, email/phone for announcements
- cancel only allowed up to 24h before the start time
- participant profile (my bookings): date, start time, meeting point, people, names
- guide profile: reservations grouped per date with total expected people
- post-tour report: for past dates with bookings, declare attendance + 1 photo
- each tour poster also shows which guide posted it
- guide: create/edit/delete tours (locked after the first booking)
- admin: optional prova finale account - counts + guides (with languages) +
  participants + all bookings. admin still has full access (can edit/delete any tour).
  it is included for the optional prova finale requirement.
- contact page + editable profile + change password + navbar dropdown

---

## extra features 

extra stuff i added beyond what was needed:

**homepage highlights** (three boxes under the hero banner):

| box | what it means |
|-----|----------------|
| free to join | tours can be free - no paywall to browse or book |
| local guides | tours are run by tehran guides, not a generic catalog |
| tehran heritage routes | themed walks around historic tehran / silk road vibe |

**ui polish**

- hero banner with gradient + tagline (*every step tells a story*)
- hero background image on the home page (`static/images/bg.jpg`)
- square tour cards (`aspect-ratio 1:1`) so the grid looks even
- photo gallery modal with prev/next arrows + keyboard (left/right keys)
- live spots-left on booking form (calls `/tour/<id>/availability` when you pick a date)
- navbar name dropdown (profile, dashboard, logout)
- form validation errors stay on the same page (not a blank 400)
- tour stops (4+ per route) on create/edit + tour detail page
- editable profile, demo forgot-password page, booking contact email/phone

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

## project structure 

```
app.py              routes + flask-login
helpers.py          small helper functions (photos, schedule, parsing) - keeps app.py short
*_dao.py            database stuff (one file per table-ish)
user_model.py       user class for flask-login
templates/          html pages
static/css/         custom styles
static/images/      home page background (bg.jpg)
static/uploads/     tour photos
schema.sql          full db structure (reference)
seed.sql            sample accounts
silkstep.db         the actual sqlite db (already filled)
credentials.txt     exam test logins
```
