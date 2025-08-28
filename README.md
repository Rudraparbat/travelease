# TravelEase

## Description
A dynamic travel website built with Django framework and neon postgresql db, designed to help users to book their travel experiences.

## Features
- User authentication and authorization
- Travel packages listing
- Booking system
- Payment integration
- Offline Booking Support 
- Booking Cancellation

## Tech Stack
- Django
- Python
- HTML
- Tailwindcss
- JavaScript
- PostgreSQL
- Docker

## Prerequisites

- Python 3.10+
- Docker Installed

## Installation And Set Up (Without Docker)
1. Clone the repository
```bash
git clone https://github.com/Rudraparbat/travelease
cd travelease
```

2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # On Linux use: source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```
#### Create A .env File In The Project Directory 
4. Add These For Better Experience To .env File

```bash
RAZORPAY_KEY_ID = 'rzp_test_31Lp1Ol0O2d1Ug'
RAZORPAY_SECRET_ID = 'AdqWbdTtjGsaBUGq3HwVkm1a'
DB_URL = "postgresql://neondb_owner:npg_Lqmvckdn84St@ep-wild-dream-adwrnroi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
DJANGO_DEBUG=True
```

5. Run Makemigrations 
```bash
python manage.py makemigrations
```
6. Run migrations
```bash
python manage.py migrate
```

7. Start development server
```bash
python manage.py runserver
```

## Set Up With Docker :- 

1. Clone the repository
```bash
git clone https://github.com/Rudraparbat/travelease
cd travelease
```

2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # On Linux use: source venv/bin/activate
```

### Befor Running The Container :- 

#### Create A .env File In The Project Directory And Follow Step No. 4 From Installation and Set-up Without Docker

3. Start The Docker Container 
```bash
docker-compose up --build
```

### Note :- If There Is Any Error Like  "web-1  | exec /app/entrypoint.prod.sh: no such file or directory" Then Change File Type From CRLF TO LF


## Local Server Always Available At :-  http://127.0.0.1:8000/ 

## SuperUser Credentials :- 
```bash
username : - admin
password :- 123
```
##  To Create Super User
```bash
python manage.py createsuperuser
```

## Run Test Cases :- 

1. To Run Test Cases :- 
```bash
coverage run manage.py test
```
2. To Generate The Coverage Report :- 
```bash
coverage html
```
3. Check The Coverage Report :- 
```bash
start htmlcov\index.html
```

## Note

- For Better Experience Run The Server From Desktop or Laptop.
- Live Link :-  https://travelease-xufv.onrender.com/