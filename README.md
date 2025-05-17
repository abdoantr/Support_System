# Support System

A comprehensive ticket-based support system built with Django 5.0, providing both a web interface and REST API for managing support tickets, services, and customer interactions.

## Features

- **User Management**: Custom user model with support for multiple roles (Admin, Technician, Customer)
- **Support Tickets**: Create, track, and manage support tickets
- **Service Catalog**: Showcase and manage available services
- **Appointments**: Schedule and manage service appointments
- **Payment Processing**: Handle service payments
- **Notifications**: Email notifications for ticket updates and assignments
- **REST API**: Full API access with documentation via Swagger/ReDoc

## Tech Stack

- **Backend**: Django 5.0, Django REST Framework
- **Database**: MySQL
- **Task Queue**: Celery with Redis
- **Frontend**: Bootstrap 5 with Django Templates
- **API Documentation**: drf-spectacular

## Setup

python -m venv .venv
source .venv/bin/activate  # On Windows: .\venv\Scripts\activate

0. create database:

```
CREATE DATABASE supportsystem;
```

```

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file (see `.env.example` for required variables)

3. Apply migrations:

```bash
python manage.py migrate
```

4. Create a superuser:

```bash
python manage.py createsuperuser
```

5. Run the development server:

```bash
python manage.py runserver
```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

## License

MIT
