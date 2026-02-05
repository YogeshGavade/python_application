# StayIndia - Hotel Booking App (India)

A complete Python Flask web application for Indian hotel booking with backend + frontend.

## Features
- Search hotels by city.
- View hotel details with amenities and pricing in INR.
- Book hotels with guest details, check-in/check-out, rooms and guest count.
- Booking confirmation with persistent storage in SQLite.
- "My Bookings" page to view reservations by email.
- Responsive frontend with custom styling and image assets.

## Tech Stack
- Python 3
- Flask
- SQLite (built-in)
- HTML/CSS (Jinja templates)

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Open: `http://localhost:5000`

## Project Structure
```
python_application/
├── app.py
├── main.py
├── requirements.txt
├── hotel_booking.db (auto-generated)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── hotel_detail.html
│   └── bookings.html
└── static/
    ├── css/styles.css
    └── img/*.svg
```
