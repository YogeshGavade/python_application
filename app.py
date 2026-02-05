from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "hotel_booking.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "india-hotel-booking-secret-key"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            area TEXT NOT NULL,
            nightly_price INTEGER NOT NULL,
            rating REAL NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT NOT NULL,
            amenities TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            guest_email TEXT NOT NULL,
            guest_phone TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            rooms INTEGER NOT NULL,
            guests INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(hotel_id) REFERENCES hotels(id)
        )
        """
    )

    count = db.execute("SELECT COUNT(*) FROM hotels").fetchone()[0]
    if count == 0:
        sample_hotels = [
            (
                "The Royal Neemrana",
                "Jaipur",
                "Civil Lines",
                5200,
                4.5,
                "Heritage-style stay with rooftop dining, close to Hawa Mahal and City Palace.",
                "jaipur.svg",
                "Free WiFi,Pool,Breakfast,Parking,Airport Pickup",
            ),
            (
                "Marine Bay Residency",
                "Mumbai",
                "Colaba",
                6800,
                4.3,
                "Modern sea-facing rooms near Gateway of India with easy local travel access.",
                "mumbai.svg",
                "Free WiFi,Gym,Breakfast,Sea View,24x7 Front Desk",
            ),
            (
                "Backwater Bloom Resort",
                "Kochi",
                "Fort Kochi",
                4500,
                4.6,
                "Calm boutique property with Kerala cuisine and sunset cruise add-ons.",
                "kochi.svg",
                "Free WiFi,Restaurant,Spa,Parking,Airport Pickup",
            ),
            (
                "Himalayan Cedar Retreat",
                "Manali",
                "Old Manali",
                3900,
                4.4,
                "Mountain-view rooms, bonfire nights, and guided adventure activities.",
                "manali.svg",
                "Free WiFi,Breakfast,Bonfire,Heater,Travel Desk",
            ),
            (
                "Coromandel Crown",
                "Chennai",
                "T Nagar",
                4100,
                4.2,
                "Business-friendly hotel near shopping districts and metro connectivity.",
                "chennai.svg",
                "Free WiFi,Breakfast,Parking,Conference Hall,24x7 Front Desk",
            ),
            (
                "Ganga View Haveli",
                "Varanasi",
                "Dashashwamedh",
                3600,
                4.7,
                "Riverside rooms, evening aarti views, and curated local heritage walks.",
                "varanasi.svg",
                "Free WiFi,Breakfast,River View,Airport Pickup,Travel Desk",
            ),
        ]
        db.executemany(
            """
            INSERT INTO hotels (name, city, area, nightly_price, rating, description, image_path, amenities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_hotels,
        )

    db.commit()
    db.close()


def parse_date(date_text: str) -> datetime:
    return datetime.strptime(date_text, "%Y-%m-%d")


def get_nights(check_in: str, check_out: str) -> int:
    return (parse_date(check_out) - parse_date(check_in)).days


@app.route("/")
def home() -> str:
    db = get_db()
    city = request.args.get("city", "")
    guests = request.args.get("guests", "2")
    check_in = request.args.get("check_in")
    check_out = request.args.get("check_out")

    query = "SELECT * FROM hotels"
    params: list[Any] = []
    if city:
        query += " WHERE city = ?"
        params.append(city)

    hotels = db.execute(query, params).fetchall()
    city_options = [
        row["city"]
        for row in db.execute("SELECT DISTINCT city FROM hotels ORDER BY city ASC").fetchall()
    ]

    return render_template(
        "index.html",
        hotels=hotels,
        city_options=city_options,
        selected_city=city,
        guests=guests,
        check_in=check_in,
        check_out=check_out,
    )


@app.route("/hotel/<int:hotel_id>", methods=["GET", "POST"])
def hotel_details(hotel_id: int) -> str:
    db = get_db()
    hotel = db.execute("SELECT * FROM hotels WHERE id = ?", (hotel_id,)).fetchone()
    if hotel is None:
        flash("Hotel not found.", "error")
        return redirect(url_for("home"))

    today = datetime.today().date()
    default_check_in = (today + timedelta(days=1)).isoformat()
    default_check_out = (today + timedelta(days=2)).isoformat()

    if request.method == "POST":
        form = request.form
        guest_name = form.get("guest_name", "").strip()
        guest_email = form.get("guest_email", "").strip().lower()
        guest_phone = form.get("guest_phone", "").strip()
        check_in = form.get("check_in", "")
        check_out = form.get("check_out", "")
        rooms = int(form.get("rooms", "1"))
        guests = int(form.get("guests", "1"))

        if not all([guest_name, guest_email, guest_phone, check_in, check_out]):
            flash("Please fill all booking details.", "error")
            return redirect(url_for("hotel_details", hotel_id=hotel_id))

        nights = get_nights(check_in, check_out)
        if nights <= 0:
            flash("Check-out date must be after check-in date.", "error")
            return redirect(url_for("hotel_details", hotel_id=hotel_id))

        total_price = nights * rooms * hotel["nightly_price"]
        db.execute(
            """
            INSERT INTO bookings (
                hotel_id, guest_name, guest_email, guest_phone,
                check_in, check_out, rooms, guests, total_price, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hotel_id,
                guest_name,
                guest_email,
                guest_phone,
                check_in,
                check_out,
                rooms,
                guests,
                total_price,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        db.commit()
        flash("Booking confirmed successfully!", "success")
        return redirect(url_for("bookings", email=guest_email))

    return render_template(
        "hotel_detail.html",
        hotel=hotel,
        default_check_in=default_check_in,
        default_check_out=default_check_out,
    )


@app.route("/bookings")
def bookings() -> str:
    email = request.args.get("email", "").strip().lower()
    booking_rows = []
    if email:
        booking_rows = get_db().execute(
            """
            SELECT b.*, h.name AS hotel_name, h.city, h.area
            FROM bookings b
            JOIN hotels h ON b.hotel_id = h.id
            WHERE b.guest_email = ?
            ORDER BY b.created_at DESC
            """,
            (email,),
        ).fetchall()
    return render_template("bookings.html", bookings=booking_rows, email=email)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
