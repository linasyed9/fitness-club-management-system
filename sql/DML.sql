INSERT INTO members (member_id, full_name, email, date_of_birth, gender, phone, registration_date) VALUES
(1, 'Ava Thompson', 'ava.member@example.com', '2001-04-12', 'Female', '613-555-1001', CURRENT_TIMESTAMP - INTERVAL '90 days'),
(2, 'Noah Bennett', 'noah.member@example.com', '1999-11-03', 'Male', '613-555-1002', CURRENT_TIMESTAMP - INTERVAL '60 days'),
(3, 'Mia Rodriguez', 'mia.member@example.com', '2002-07-19', 'Female', '613-555-1003', CURRENT_TIMESTAMP - INTERVAL '30 days');

INSERT INTO trainers (trainer_id, full_name, email, phone, specialization) VALUES
(1, 'Ethan Carter', 'ethan.trainer@example.com', '613-555-2001', 'Strength Training'),
(2, 'Sophia Lee', 'sophia.trainer@example.com', '613-555-2002', 'Yoga and Mobility');

INSERT INTO admin_staff (admin_id, full_name, email, phone) VALUES
(1, 'Olivia Parker', 'olivia.admin@example.com', '613-555-3001');

INSERT INTO users (user_id, email, password_hash, role, linked_id) VALUES
(1, 'ava.member@example.com', 'pbkdf2:sha256:600000$5afa6224e33e2e5a$980767c677b54300d6e89452a3eaae95370e5142b8ab49fb8f5690eeb764d865', 'member', 1),
(2, 'noah.member@example.com', 'pbkdf2:sha256:600000$a4218adc69ae5a09$e27c05f6a97d5ddad69d8a330df7d3780af7e6e0f896a8e3569f9ede5867e9ff', 'member', 2),
(3, 'mia.member@example.com', 'pbkdf2:sha256:600000$a9e59ab71e4708d6$e8e956b23de964995c8736c62ac6c1d786ab872b33a482bbc59d282c0dbc7c5e', 'member', 3),
(4, 'ethan.trainer@example.com', 'pbkdf2:sha256:600000$16cdf5586d812ee9$a1d710b76788ceb1a1b06b9e03eb5db7eeed743612e4b1f84280f98436ac1800', 'trainer', 1),
(5, 'sophia.trainer@example.com', 'pbkdf2:sha256:600000$b40635f0c813e8d8$505ba9f60500f4228d443b9fdaaddb1560debb1ca7b6971c4e842b4698d335aa', 'trainer', 2),
(6, 'olivia.admin@example.com', 'pbkdf2:sha256:600000$c941b328629662d6$2c983f23dc90fab0ea49f13407d6dcb2ea63597cafc5e55f9917b52f325fd34b', 'admin', 1);

INSERT INTO fitness_goals (goal_id, member_id, goal_description, target_value, created_at) VALUES
(1, 1, 'Lose body weight steadily', '65 kg', CURRENT_TIMESTAMP - INTERVAL '20 days'),
(2, 1, 'Improve resting heart rate', 'Below 65 bpm', CURRENT_TIMESTAMP - INTERVAL '10 days'),
(3, 2, 'Increase bench press strength', '100 kg', CURRENT_TIMESTAMP - INTERVAL '15 days'),
(4, 3, 'Complete 5 km run comfortably', 'Under 30 minutes', CURRENT_TIMESTAMP - INTERVAL '12 days');

INSERT INTO health_metrics (metric_id, member_id, metric_type, value, recorded_at) VALUES
(1, 1, 'weight', 72.40, CURRENT_TIMESTAMP - INTERVAL '14 days'),
(2, 1, 'weight', 70.80, CURRENT_TIMESTAMP - INTERVAL '2 days'),
(3, 1, 'heart_rate', 72.00, CURRENT_TIMESTAMP - INTERVAL '5 days'),
(4, 2, 'weight', 82.10, CURRENT_TIMESTAMP - INTERVAL '9 days'),
(5, 2, 'heart_rate', 68.00, CURRENT_TIMESTAMP - INTERVAL '1 days'),
(6, 3, 'weight', 61.50, CURRENT_TIMESTAMP - INTERVAL '7 days'),
(7, 3, 'heart_rate', 75.00, CURRENT_TIMESTAMP - INTERVAL '3 days');

INSERT INTO rooms (room_id, room_name, capacity, location) VALUES
(1, 'Studio A', 20, 'Athletics Building - First Floor'),
(2, 'Weight Room', 15, 'Athletics Building - Ground Floor');

INSERT INTO trainer_availability (availability_id, trainer_id, available_date, start_time, end_time) VALUES
(1, 1, '2026-04-01', '09:00', '12:00'),
(2, 1, '2026-04-02', '13:00', '16:00'),
(3, 2, '2026-04-01', '10:00', '13:00'),
(4, 2, '2026-04-03', '14:00', '17:00');

INSERT INTO personal_training_sessions (session_id, member_id, trainer_id, room_id, session_date, start_time, end_time, status) VALUES
(1, 1, 1, 2, '2026-04-01', '09:00', '10:00', 'scheduled'),
(2, 2, 2, 1, '2026-04-03', '14:00', '15:00', 'scheduled');

INSERT INTO group_classes (class_id, class_name, trainer_id, room_id, class_date, start_time, end_time, capacity) VALUES
(1, 'Morning HIIT', 1, 1, '2026-03-20', '08:00', '09:00', 2),
(2, 'Evening Yoga', 2, 1, '2026-04-02', '18:00', '19:00', 3),
(3, 'Strength Fundamentals', 1, 2, '2026-04-04', '11:00', '12:00', 4);

INSERT INTO class_enrollments (enrollment_id, class_id, member_id, enrolled_at) VALUES
(1, 1, 1, CURRENT_TIMESTAMP - INTERVAL '8 days'),
(2, 1, 2, CURRENT_TIMESTAMP - INTERVAL '8 days'),
(3, 2, 3, CURRENT_TIMESTAMP - INTERVAL '1 days');

INSERT INTO equipment (equipment_id, name, room_id, status, last_updated) VALUES
(1, 'Treadmill 1', 1, 'operational', CURRENT_TIMESTAMP - INTERVAL '2 days'),
(2, 'Rowing Machine 2', 1, 'under repair', CURRENT_TIMESTAMP - INTERVAL '1 days'),
(3, 'Bench Press Station', 2, 'operational', CURRENT_TIMESTAMP - INTERVAL '4 days'),
(4, 'Elliptical 3', 1, 'out of service', CURRENT_TIMESTAMP - INTERVAL '6 hours');

INSERT INTO billing (billing_id, member_id, amount, payment_status, payment_date, payment_method) VALUES
(1, 1, 59.99, 'paid', '2026-03-01', 'credit card'),
(2, 2, 59.99, 'paid', '2026-03-01', 'debit'),
(3, 3, 59.99, 'pending', '2026-03-15', 'cash');

SELECT setval(pg_get_serial_sequence('members', 'member_id'), COALESCE(MAX(member_id), 1)) FROM members;
SELECT setval(pg_get_serial_sequence('trainers', 'trainer_id'), COALESCE(MAX(trainer_id), 1)) FROM trainers;
SELECT setval(pg_get_serial_sequence('admin_staff', 'admin_id'), COALESCE(MAX(admin_id), 1)) FROM admin_staff;
SELECT setval(pg_get_serial_sequence('users', 'user_id'), COALESCE(MAX(user_id), 1)) FROM users;
SELECT setval(pg_get_serial_sequence('fitness_goals', 'goal_id'), COALESCE(MAX(goal_id), 1)) FROM fitness_goals;
SELECT setval(pg_get_serial_sequence('health_metrics', 'metric_id'), COALESCE(MAX(metric_id), 1)) FROM health_metrics;
SELECT setval(pg_get_serial_sequence('rooms', 'room_id'), COALESCE(MAX(room_id), 1)) FROM rooms;
SELECT setval(pg_get_serial_sequence('trainer_availability', 'availability_id'), COALESCE(MAX(availability_id), 1)) FROM trainer_availability;
SELECT setval(pg_get_serial_sequence('personal_training_sessions', 'session_id'), COALESCE(MAX(session_id), 1)) FROM personal_training_sessions;
SELECT setval(pg_get_serial_sequence('group_classes', 'class_id'), COALESCE(MAX(class_id), 1)) FROM group_classes;
SELECT setval(pg_get_serial_sequence('class_enrollments', 'enrollment_id'), COALESCE(MAX(enrollment_id), 1)) FROM class_enrollments;
SELECT setval(pg_get_serial_sequence('equipment', 'equipment_id'), COALESCE(MAX(equipment_id), 1)) FROM equipment;
SELECT setval(pg_get_serial_sequence('billing', 'billing_id'), COALESCE(MAX(billing_id), 1)) FROM billing;

-- Demo note for the trigger failure case:
-- The following insert should fail with: Class is full
-- INSERT INTO class_enrollments (class_id, member_id) VALUES (1, 3);
