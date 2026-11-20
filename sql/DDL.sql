DROP VIEW IF EXISTS member_dashboard_view;
DROP TRIGGER IF EXISTS prevent_class_overbooking ON class_enrollments;
DROP FUNCTION IF EXISTS prevent_class_overbooking();
DROP TYPE IF EXISTS user_role;

DROP TABLE IF EXISTS billing CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS class_enrollments CASCADE;
DROP TABLE IF EXISTS group_classes CASCADE;
DROP TABLE IF EXISTS personal_training_sessions CASCADE;
DROP TABLE IF EXISTS trainer_availability CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS health_metrics CASCADE;
DROP TABLE IF EXISTS fitness_goals CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS admin_staff CASCADE;
DROP TABLE IF EXISTS trainers CASCADE;
DROP TABLE IF EXISTS members CASCADE;

CREATE TYPE user_role AS ENUM ('member', 'trainer', 'admin');

CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(30) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trainers (
    trainer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL,
    specialization VARCHAR(100) NOT NULL
);

CREATE TABLE admin_staff (
    admin_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role user_role NOT NULL,
    linked_id INTEGER NOT NULL
);

CREATE TABLE fitness_goals (
    goal_id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    goal_description TEXT NOT NULL,
    target_value VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE health_metrics (
    metric_id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    location VARCHAR(100) NOT NULL
);

CREATE TABLE trainer_availability (
    availability_id SERIAL PRIMARY KEY,
    trainer_id INTEGER NOT NULL REFERENCES trainers(trainer_id) ON DELETE CASCADE,
    available_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    CHECK (end_time > start_time)
);

CREATE TABLE personal_training_sessions (
    session_id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    trainer_id INTEGER NOT NULL REFERENCES trainers(trainer_id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(room_id) ON DELETE SET NULL,
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled',
    CHECK (end_time > start_time)
);

CREATE TABLE group_classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    trainer_id INTEGER NOT NULL REFERENCES trainers(trainer_id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(room_id) ON DELETE SET NULL,
    class_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    CHECK (end_time > start_time)
);

CREATE TABLE class_enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES group_classes(class_id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (class_id, member_id)
);

CREATE TABLE equipment (
    equipment_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    room_id INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL CHECK (status IN ('operational', 'under repair', 'out of service')),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE billing (
    billing_id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    payment_status VARCHAR(30) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL
);

CREATE INDEX idx_health_metrics_member_recorded_at
ON health_metrics(member_id, recorded_at DESC);

CREATE OR REPLACE FUNCTION prevent_class_overbooking()
RETURNS TRIGGER AS $$
DECLARE
    current_enrolled INTEGER;
    max_capacity INTEGER;
BEGIN
    SELECT capacity
    INTO max_capacity
    FROM group_classes
    WHERE class_id = NEW.class_id
    FOR UPDATE;

    IF max_capacity IS NULL THEN
        RAISE EXCEPTION 'Class does not exist';
    END IF;

    SELECT COUNT(*)
    INTO current_enrolled
    FROM class_enrollments
    WHERE class_id = NEW.class_id;

    IF current_enrolled >= max_capacity THEN
        RAISE EXCEPTION 'Class is full';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_class_overbooking
BEFORE INSERT ON class_enrollments
FOR EACH ROW
EXECUTE FUNCTION prevent_class_overbooking();

CREATE VIEW member_dashboard_view AS
SELECT
    m.member_id,
    m.full_name AS member_name,
    fg.goal_id,
    fg.goal_description,
    fg.target_value,
    fg.created_at AS goal_created_at,
    hm.metric_id,
    hm.metric_type,
    hm.value AS metric_value,
    hm.recorded_at AS metric_recorded_at,
    pts.session_id,
    pts.session_date,
    pts.start_time AS session_start_time,
    pts.end_time AS session_end_time,
    pts.status AS session_status,
    t.trainer_id,
    t.full_name AS trainer_name,
    (
        SELECT COUNT(*)
        FROM class_enrollments ce
        JOIN group_classes gc2 ON gc2.class_id = ce.class_id
        WHERE ce.member_id = m.member_id
          AND gc2.class_date < CURRENT_DATE
    ) AS total_classes_attended
FROM members m
LEFT JOIN fitness_goals fg ON fg.member_id = m.member_id
LEFT JOIN health_metrics hm ON hm.member_id = m.member_id
LEFT JOIN personal_training_sessions pts
    ON pts.member_id = m.member_id
   AND pts.session_date >= CURRENT_DATE
   AND pts.status = 'scheduled'
LEFT JOIN trainers t ON t.trainer_id = pts.trainer_id;
