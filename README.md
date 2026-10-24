# Smart Blood Donor Finder

A Django web application that connects blood donors with people who need blood.

**Live demo:** https://nikkiyadav.pythonanywhere.com

## Features

- Donor registration with validation (age 18-65) and consent checkbox
- Login and logout
- Donor list and detail pages
- Search donors by blood group and city
- Availability status based on a 90-day gap between donations
- Phone numbers visible only to logged-in users
- Blood request posting, with an option to mark requests as fulfilled
- Statistics page with a Matplotlib chart of donors per blood group
- 33 automated tests

## Tech Stack

- Python, Django 5.2
- SQLite
- Matplotlib
- HTML and CSS
- Hosted on PythonAnywhere

## Run Locally

1. Clone the repository:
   git clone https://github.com/Nikkiyadav1130/blood-donor-finder.git
2. Create and activate a virtual environment:
   python -m venv venv
   venv\Scripts\activate
3. Install dependencies:
   pip install -r requirements.txt
4. Set up the database:
   python manage.py migrate
5. Create an admin user:
   python manage.py createsuperuser
6. Start the server:
   python manage.py runserver

## Run Tests

python manage.py test

## Author

Nikki Yadav, B.Tech CSE, MIT Moradabad