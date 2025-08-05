# SpiceRoute

SpiceRoute is a modern B2B web platform designed to streamline the procurement of raw materials for small vendors directly from verified micro-suppliers. Built using Django and Bootstrap, it offers an intuitive, region-aware, and responsive user experience.

---

## Features

- Vendor & Supplier Dashboards with Authentication
- Product Listings with Category & Search Filtering
- Voice-based Search (Multi-language support)
- Real-Time Bargain Contact Option with Suppliers
- Cart Management & Checkout Flow
- Supplier Listings Management & Performance View
- Vendor Booking History and Purchase Summaries
- Secure Role-Based Access

---

## Folder Structure



SPICEROUTE/
├── spice-route-venv/       # Python virtual environment
├── spiceroute/             # Django project folder
│   ├── spiceroute/         # Core Django app
│   │   ├── templates/      # HTML templates
│   │   ├── templatetags/   # Custom template tags (if any)
│   │   ├── views.py        # All views
│   │   ├── models.py       # Data models
│   │   ├── urls.py         # URL routing
│   │   └── settings.py     # Django settings
├── db.sqlite3              # SQLite3 database
├── manage.py               # Django management file
├── requirements.txt        # All project dependencies
└── README.md               # Project documentation



---

## Installation & Setup

1. **Clone the repository**
   git clone https://github.com/manaswi-siripurapu/SpiceRoute.git
   cd SpiceRoute


2. **Create virtual environment**
   python -m venv .spice-route-venv
   .spice-route-venv\Scripts\activate   # Windows

3. **Install dependencies**
   pip install -r requirements.txt
   cd spiceroute

4. **Run migrations**
   python manage.py makemigrations
   python manage.py migrate

5. **Start the development server**
   python manage.py runserver

6. **Access the app**
   Open `http://127.0.0.1:8000/` in your browser.

---

## Voice Search Support

* Languages supported: English, Hindi, Telugu, Tamil, Bengali
* Works best on Chromium-based browsers with mic access

---

## Tech Stack

* **Backend**: Django, SQLite
* **Frontend**: HTML, Bootstrap, JavaScript
* **Voice Recognition**: Web Speech API (browser-based)
* **Version Control**: Git, GitHub

---

## License

This project is for educational and demonstration purposes only. All rights reserved by the original authors.

---

## Team

Developed with dedication during a hackathon sprint by
**Manaswi Siripurapu** and team.
