<div align="center">

# SilkStep

### Every step tells a story.

A full-stack platform for discovering, publishing, and booking local walking tours in Tehran.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)

**[Run locally](#run-locally)** · **[Explore features](#core-features)** · **[View architecture](#technical-overview)**

</div>

![SilkStep homepage with a Tehran tour hero and featured walking tours](static/images/homepage-preview.png)

## Overview

SilkStep connects local guides with people looking for themed walking tours. Guides manage tour content and schedules, participants book a date and party size, and administrators review platform activity.

The project demonstrates an end-to-end web workflow: role-based authentication, relational data, business-rule validation, image handling, responsive server-rendered pages, and dashboards for three user types.

> Built by **Mohamad Keshmiri** for *Introduction to Web Applications*, 2025/2026. This repository is a coursework project, not a production booking service.

## Core features

- **Tour discovery** — browse Tehran routes and filter by date, duration, and language
- **Guide workspace** — publish tours, manage schedules, review reservations, and submit post-tour reports
- **Participant booking** — choose a tour date, reserve for 1–4 people, and manage upcoming bookings
- **Capacity rules** — availability is calculated per tour date and validated before each booking
- **Role-based access** — separate participant, guide, and administrator permissions
- **Admin overview** — inspect users, tours, bookings, and platform totals
- **Operational safeguards** — cancellation deadlines and content locks after the first booking

## Technical overview

| Area | Implementation |
| --- | --- |
| Backend | Python, Flask, Flask-Login |
| Data | SQLite, SQL schema and seed data, domain-specific DAO modules |
| Frontend | Jinja templates, Bootstrap 5, custom CSS and JavaScript |
| Authentication | Session-based login with role checks on protected routes |
| Validation | Server-side capacity, schedule, ownership, and deadline rules |
| Media | Tour galleries, promotional images, and post-tour photo uploads |

```text
Browser → Flask routes → validation and role checks → DAO modules → SQLite
              ↓
       Jinja templates + Bootstrap UI
```

## Run locally

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate it with `.venv\Scripts\activate`.

### 2. Install and start

```bash
pip install -r requirements.txt
python3 app.py
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001). The included SQLite database already contains sample tours and accounts.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Guide | `guide1@test.com` | `pass123` |
| Participant | `user1@test.com` | `pass123` |
| Admin | `admin@test.com` | `admin123` |

Additional sample logins are listed in `credentials.txt`. These credentials are for local demonstration only.

## Project structure

```text
app.py              Flask routes and application setup
helpers.py          schedule, image, and parsing helpers
*_dao.py            database access grouped by domain
user_model.py       Flask-Login user model
templates/          server-rendered pages
static/css/         application styles
static/images/      interface and README images
static/uploads/     sample tour media
schema.sql          database structure
seed.sql            sample records
silkstep.db         ready-to-run local database
```

## Selected UI details

- Responsive tour grid and Tehran-inspired visual identity
- Image gallery with keyboard and previous/next navigation
- Live availability feedback on the booking form
- Context-aware navigation for each authenticated role
- Inline validation that keeps submitted values on the page

## License

[MIT](LICENSE) © 2026 Mo Keshmiri
