# Health and Fitness Club Management System

## Tech Stack

- PostgreSQL
- Python 3
- Flask
- psycopg2
- Plain HTML/CSS

## Implemented Roles

- Member
- Trainer
- Administrative Staff

## Implemented Course Operations

1. User Registration
2. Profile Management
3. Health History
4. Dashboard
5. Set Availability
6. Schedule View
7. Room Booking
8. Equipment Maintenance

## Project Structure

```text
fitness_club/
├── app.py
├── db.py
├── requirements.txt
├── README.md
├── sql/
│   ├── DDL.sql
│   └── DML.sql
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── member/
    │   ├── dashboard.html
    │   ├── profile.html
    │   └── health_history.html
    ├── trainer/
    │   ├── availability.html
    │   └── schedule.html
    └── admin/
        ├── room_booking.html
        └── equipment.html
```

## Database Setup

### 1. Create the database

Open PostgreSQL and run:

```sql
CREATE DATABASE fitness_club_db;
```

### 2. Configure connection settings

The app reads these environment variables:

- `DB_HOST` (default: `localhost`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `fitness_club_db`)
- `DB_USER` (default: `postgres`)
- `DB_PASSWORD` (default: `postgres`)


### 3. Load schema and sample data

From the project root:

```bash
psql -U postgres -d fitness_club_db -f sql/DDL.sql
psql -U postgres -d fitness_club_db -f sql/DML.sql
```

If your PostgreSQL user is not `postgres`, replace it with your username.

## Python Setup

### 1. Create and activate a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Flask app

```bash
python app.py
```

The application runs at:

```text
http://127.0.0.1:5000
```

## Seeded Login Accounts

All seeded accounts use this password:

```text
password123
```

### Members

- `ava.member@example.com`
- `noah.member@example.com`
- `mia.member@example.com`

### Trainers

- `ethan.trainer@example.com`
- `sophia.trainer@example.com`

### Administrative Staff

- `olivia.admin@example.com`

## Notes for Demonstration

### Trigger demonstration
The trigger `prevent_class_overbooking` is created in `sql/DDL.sql`.

Class `class_id = 1` is already full after the seed inserts. Running this statement should raise the required error:

```sql
INSERT INTO class_enrollments (class_id, member_id) VALUES (1, 3);
```

Expected PostgreSQL error message:

```text
Class is full
```

### Failure cases you can demo in the web app

- Register with an existing email address
- Add a trainer availability slot that overlaps an existing one
- Add a trainer availability slot where end time is not later than start time
- Assign a room to a booking that conflicts with another booking
- Submit empty profile, goal, or metric fields
- Update equipment with an invalid status using form tampering