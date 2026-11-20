import os
from functools import wraps
from datetime import date

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from psycopg2 import IntegrityError

from db import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-me')


ROLE_DASHBOARD = {
    'member': 'member_dashboard',
    'trainer': 'trainer_schedule',
    'admin': 'admin_room_booking',
}


@app.context_processor
def inject_globals():
    return {'today': date.today()}


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'error')
                return redirect(url_for('login'))
            if session.get('role') != required_role:
                flash('You are not authorized to access that page.', 'error')
                target = ROLE_DASHBOARD.get(session.get('role'))
                if target:
                    return redirect(url_for(target))
                return redirect(url_for('login'))
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


@app.route('/')
def index():
    if 'role' in session:
        return redirect(url_for(ROLE_DASHBOARD[session['role']]))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'role' in session:
        return redirect(url_for(ROLE_DASHBOARD[session['role']]))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, email, password_hash, role, linked_id
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    """,
                    (email,),
                )
                user = cur.fetchone()

            if not user or not check_password_hash(user['password_hash'], password):
                flash('Invalid email or password.', 'error')
                return render_template('login.html')

            session.clear()
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['linked_id'] = user['linked_id']
            flash('Logged in successfully.', 'success')
            return redirect(url_for(ROLE_DASHBOARD[user['role']]))
        except Exception:
            flash('Unable to log in right now. Please try again.', 'error')
        finally:
            if conn:
                conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        date_of_birth = request.form.get('date_of_birth', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if not all([full_name, email, date_of_birth, gender, phone, password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT 1 FROM users WHERE LOWER(email) = LOWER(%s)',
                    (email,),
                )
                if cur.fetchone():
                    flash('Email already registered.', 'error')
                    return render_template('register.html')

                cur.execute(
                    """
                    INSERT INTO members (full_name, email, date_of_birth, gender, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING member_id
                    """,
                    (full_name, email, date_of_birth, gender, phone),
                )
                member = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO users (email, password_hash, role, linked_id)
                    VALUES (%s, %s, 'member', %s)
                    """,
                    (email, generate_password_hash(password), member['member_id']),
                )
            conn.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            if conn:
                conn.rollback()
            flash('Email already registered.', 'error')
        except Exception:
            if conn:
                conn.rollback()
            flash('Registration failed. Please verify your details and try again.', 'error')
        finally:
            if conn:
                conn.close()

    return render_template('register.html')


@app.route('/member/profile', methods=['GET', 'POST'])
@login_required
@role_required('member')
def member_profile():
    member_id = session['linked_id']
    conn = None

    try:
        conn = get_db_connection()

        if request.method == 'POST':
            action = request.form.get('action', '').strip()

            try:
                with conn.cursor() as cur:
                    if action == 'update_profile':
                        full_name = request.form.get('full_name', '').strip()
                        phone = request.form.get('phone', '').strip()

                        if not full_name or not phone:
                            flash('Full name and phone are required.', 'error')
                        else:
                            cur.execute(
                                """
                                UPDATE members
                                SET full_name = %s, phone = %s
                                WHERE member_id = %s
                                """,
                                (full_name, phone, member_id),
                            )
                            conn.commit()
                            flash('Profile updated successfully.', 'success')

                    elif action == 'add_goal':
                        goal_description = request.form.get('goal_description', '').strip()
                        target_value = request.form.get('target_value', '').strip()

                        if not goal_description or not target_value:
                            flash('Goal description and target value are required.', 'error')
                        else:
                            cur.execute(
                                """
                                INSERT INTO fitness_goals (member_id, goal_description, target_value)
                                VALUES (%s, %s, %s)
                                """,
                                (member_id, goal_description, target_value),
                            )
                            conn.commit()
                            flash('Fitness goal added successfully.', 'success')

                    elif action == 'update_goal':
                        goal_id = request.form.get('goal_id', '').strip()
                        goal_description = request.form.get('goal_description', '').strip()
                        target_value = request.form.get('target_value', '').strip()

                        if not goal_id or not goal_description or not target_value:
                            flash('Goal description and target value are required.', 'error')
                        else:
                            cur.execute(
                                """
                                UPDATE fitness_goals
                                SET goal_description = %s,
                                    target_value = %s
                                WHERE goal_id = %s
                                  AND member_id = %s
                                """,
                                (goal_description, target_value, goal_id, member_id),
                            )
                            conn.commit()

                            if cur.rowcount:
                                flash('Fitness goal updated successfully.', 'success')
                            else:
                                flash('Fitness goal not found.', 'error')

                    elif action == 'add_metric':
                        metric_type = request.form.get('metric_type', '').strip()
                        value = request.form.get('value', '').strip()

                        if not metric_type or not value:
                            flash('Metric type and value are required.', 'error')
                        else:
                            cur.execute(
                                """
                                INSERT INTO health_metrics (member_id, metric_type, value)
                                VALUES (%s, %s, %s)
                                """,
                                (member_id, metric_type, value),
                            )
                            conn.commit()
                            flash('Health metric logged successfully.', 'success')

                    else:
                        flash('Invalid request.', 'error')

            except Exception:
                conn.rollback()
                flash('Unable to save your changes. Please try again.', 'error')

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT member_id, full_name, email, date_of_birth, gender, phone, registration_date
                FROM members
                WHERE member_id = %s
                """,
                (member_id,),
            )
            member = cur.fetchone()

            cur.execute(
                """
                SELECT goal_id, goal_description, target_value, created_at
                FROM fitness_goals
                WHERE member_id = %s
                ORDER BY created_at DESC
                """,
                (member_id,),
            )
            goals = cur.fetchall()

            cur.execute(
                """
                SELECT metric_id, metric_type, value, recorded_at
                FROM health_metrics
                WHERE member_id = %s
                ORDER BY recorded_at DESC
                LIMIT 10
                """,
                (member_id,),
            )
            recent_metrics = cur.fetchall()

        return render_template(
            'member/profile.html',
            member=member,
            goals=goals,
            recent_metrics=recent_metrics,
        )
    except Exception:
        flash('Unable to load your profile right now.', 'error')
        return render_template('member/profile.html', member=None, goals=[], recent_metrics=[])
    finally:
        if conn:
            conn.close()


@app.route('/member/health-history')
@login_required
@role_required('member')
def member_health_history():
    member_id = session['linked_id']
    metrics = []
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT metric_type, value, recorded_at
                FROM health_metrics
                WHERE member_id = %s
                ORDER BY recorded_at DESC
                """,
                (member_id,),
            )
            metrics = cur.fetchall()
    except Exception:
        flash('Unable to load your health history.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template('member/health_history.html', metrics=metrics)


@app.route('/member/dashboard')
@login_required
@role_required('member')
def member_dashboard():
    member_id = session['linked_id']
    dashboard_rows = []
    latest_metrics = {}
    goals = {}
    upcoming_sessions = {}
    member_name = None
    total_classes_attended = 0
    conn = None

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM member_dashboard_view
                WHERE member_id = %s
                ORDER BY metric_recorded_at DESC NULLS LAST,
                         session_date ASC NULLS LAST,
                         session_start_time ASC NULLS LAST,
                         goal_created_at DESC NULLS LAST
                """,
                (member_id,),
            )
            dashboard_rows = cur.fetchall()

        if dashboard_rows:
            member_name = dashboard_rows[0]['member_name']
            total_classes_attended = dashboard_rows[0]['total_classes_attended'] or 0

        for row in dashboard_rows:
            if row.get('metric_type') and row.get('metric_recorded_at'):
                existing = latest_metrics.get(row['metric_type'])
                if not existing or row['metric_recorded_at'] > existing['metric_recorded_at']:
                    latest_metrics[row['metric_type']] = {
                        'metric_type': row['metric_type'],
                        'metric_value': row['metric_value'],
                        'metric_recorded_at': row['metric_recorded_at'],
                    }

            if row.get('goal_id'):
                goals[row['goal_id']] = {
                    'goal_description': row['goal_description'],
                    'target_value': row['target_value'],
                    'goal_created_at': row['goal_created_at'],
                }

            if row.get('session_id') and row.get('session_date'):
                key = row['session_id']
                upcoming_sessions[key] = {
                    'session_date': row['session_date'],
                    'start_time': row['session_start_time'],
                    'end_time': row['session_end_time'],
                    'trainer_name': row['trainer_name'],
                }

        return render_template(
            'member/dashboard.html',
            member_name=member_name,
            latest_metrics=list(latest_metrics.values()),
            goals=list(goals.values()),
            total_classes_attended=total_classes_attended,
            upcoming_sessions=sorted(
                upcoming_sessions.values(),
                key=lambda item: (item['session_date'], item['start_time']),
            ),
        )
    except Exception:
        flash('Unable to load the dashboard.', 'error')
        return render_template(
            'member/dashboard.html',
            member_name=None,
            latest_metrics=[],
            goals=[],
            total_classes_attended=0,
            upcoming_sessions=[],
        )
    finally:
        if conn:
            conn.close()


@app.route('/trainer/availability', methods=['GET', 'POST'])
@login_required
@role_required('trainer')
def trainer_availability():
    trainer_id = session['linked_id']
    conn = None

    try:
        conn = get_db_connection()

        if request.method == 'POST':
            action = request.form.get('action', '').strip()

            try:
                with conn.cursor() as cur:
                    if action == 'add_slot':
                        available_date = request.form.get('available_date', '').strip()
                        start_time = request.form.get('start_time', '').strip()
                        end_time = request.form.get('end_time', '').strip()

                        if not available_date or not start_time or not end_time:
                            flash('All availability fields are required.', 'error')
                        elif end_time <= start_time:
                            flash('End time must be later than start time.', 'error')
                        else:
                            cur.execute(
                                """
                                SELECT 1
                                FROM trainer_availability
                                WHERE trainer_id = %s
                                  AND available_date = %s
                                  AND %s < end_time
                                  AND %s > start_time
                                """,
                                (trainer_id, available_date, start_time, end_time),
                            )
                            if cur.fetchone():
                                flash('Overlapping availability slot detected.', 'error')
                            else:
                                cur.execute(
                                    """
                                    INSERT INTO trainer_availability (trainer_id, available_date, start_time, end_time)
                                    VALUES (%s, %s, %s, %s)
                                    """,
                                    (trainer_id, available_date, start_time, end_time),
                                )
                                conn.commit()
                                flash('Availability slot added successfully.', 'success')

                    elif action == 'update_slot':
                        availability_id = request.form.get('availability_id', '').strip()
                        available_date = request.form.get('available_date', '').strip()
                        start_time = request.form.get('start_time', '').strip()
                        end_time = request.form.get('end_time', '').strip()

                        if not availability_id or not available_date or not start_time or not end_time:
                            flash('All availability fields are required.', 'error')
                        elif end_time <= start_time:
                            flash('End time must be later than start time.', 'error')
                        else:
                            cur.execute(
                                """
                                SELECT 1
                                FROM trainer_availability
                                WHERE trainer_id = %s
                                  AND available_date = %s
                                  AND %s < end_time
                                  AND %s > start_time
                                  AND availability_id <> %s
                                """,
                                (trainer_id, available_date, start_time, end_time, availability_id),
                            )
                            if cur.fetchone():
                                flash('Overlapping availability slot detected.', 'error')
                            else:
                                cur.execute(
                                    """
                                    UPDATE trainer_availability
                                    SET available_date = %s,
                                        start_time = %s,
                                        end_time = %s
                                    WHERE availability_id = %s
                                      AND trainer_id = %s
                                    """,
                                    (available_date, start_time, end_time, availability_id, trainer_id),
                                )
                                conn.commit()

                                if cur.rowcount:
                                    flash('Availability slot updated successfully.', 'success')
                                else:
                                    flash('Availability slot not found.', 'error')

                    elif action == 'delete_slot':
                        availability_id = request.form.get('availability_id', '').strip()

                        cur.execute(
                            """
                            DELETE FROM trainer_availability
                            WHERE availability_id = %s
                              AND trainer_id = %s
                            """,
                            (availability_id, trainer_id),
                        )
                        conn.commit()

                        if cur.rowcount:
                            flash('Availability slot deleted successfully.', 'success')
                        else:
                            flash('Availability slot not found.', 'error')

                    else:
                        flash('Invalid request.', 'error')

            except Exception:
                conn.rollback()
                flash('Unable to update availability right now.', 'error')

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT availability_id, available_date, start_time, end_time
                FROM trainer_availability
                WHERE trainer_id = %s
                ORDER BY available_date ASC, start_time ASC
                """,
                (trainer_id,),
            )
            slots = cur.fetchall()

        return render_template('trainer/availability.html', slots=slots)
    except Exception:
        flash('Unable to load availability information.', 'error')
        return render_template('trainer/availability.html', slots=[])
    finally:
        if conn:
            conn.close()


@app.route('/trainer/schedule')
@login_required
@role_required('trainer')
def trainer_schedule():
    trainer_id = session['linked_id']
    personal_sessions = []
    group_classes = []
    conn = None

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pts.session_date, pts.start_time, pts.end_time,
                       m.full_name AS member_name,
                       COALESCE(r.room_name || ' (' || r.location || ')', 'Unassigned') AS room_label
                FROM personal_training_sessions pts
                JOIN members m ON m.member_id = pts.member_id
                LEFT JOIN rooms r ON r.room_id = pts.room_id
                WHERE pts.trainer_id = %s
                  AND pts.session_date >= CURRENT_DATE
                ORDER BY pts.session_date ASC, pts.start_time ASC
                """,
                (trainer_id,),
            )
            personal_sessions = cur.fetchall()

            cur.execute(
                """
                SELECT gc.class_date, gc.start_time, gc.end_time, gc.class_name,
                       COALESCE(r.room_name || ' (' || r.location || ')', 'Unassigned') AS room_label
                FROM group_classes gc
                LEFT JOIN rooms r ON r.room_id = gc.room_id
                WHERE gc.trainer_id = %s
                  AND gc.class_date >= CURRENT_DATE
                ORDER BY gc.class_date ASC, gc.start_time ASC
                """,
                (trainer_id,),
            )
            group_classes = cur.fetchall()
    except Exception:
        flash('Unable to load schedule information.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template(
        'trainer/schedule.html',
        personal_sessions=personal_sessions,
        group_classes=group_classes,
    )


@app.route('/admin/room-booking', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_room_booking():
    rooms = []
    personal_sessions = []
    group_classes = []
    conn = None

    try:
        conn = get_db_connection()

        if request.method == 'POST':
            booking_type = request.form.get('booking_type', '').strip()
            booking_id = request.form.get('booking_id', '').strip()
            room_id = request.form.get('room_id', '').strip()

            try:
                with conn.cursor() as cur:
                    if booking_type == 'personal':
                        cur.execute(
                            """
                            SELECT session_id AS booking_id, session_date AS booking_date,
                                   start_time, end_time, room_id
                            FROM personal_training_sessions
                            WHERE session_id = %s
                            """,
                            (booking_id,),
                        )
                        booking = cur.fetchone()
                        if not booking:
                            flash('Personal training session not found.', 'error')
                        else:
                            cur.execute(
                                """
                                SELECT 1
                                FROM personal_training_sessions
                                WHERE room_id = %s
                                  AND session_date = %s
                                  AND %s < end_time
                                  AND %s > start_time
                                  AND session_id <> %s
                                UNION ALL
                                SELECT 1
                                FROM group_classes
                                WHERE room_id = %s
                                  AND class_date = %s
                                  AND %s < end_time
                                  AND %s > start_time
                                LIMIT 1
                                """,
                                (
                                    room_id,
                                    booking['booking_date'],
                                    booking['start_time'],
                                    booking['end_time'],
                                    booking['booking_id'],
                                    room_id,
                                    booking['booking_date'],
                                    booking['start_time'],
                                    booking['end_time'],
                                ),
                            )
                            if cur.fetchone():
                                flash('Room already booked at that time.', 'error')
                            else:
                                cur.execute(
                                    """
                                    UPDATE personal_training_sessions
                                    SET room_id = %s
                                    WHERE session_id = %s
                                    """,
                                    (room_id, booking_id),
                                )
                                conn.commit()
                                flash('Room assignment updated successfully.', 'success')
                    elif booking_type == 'group':
                        cur.execute(
                            """
                            SELECT class_id AS booking_id, class_date AS booking_date,
                                   start_time, end_time, room_id
                            FROM group_classes
                            WHERE class_id = %s
                            """,
                            (booking_id,),
                        )
                        booking = cur.fetchone()
                        if not booking:
                            flash('Group class not found.', 'error')
                        else:
                            cur.execute(
                                """
                                SELECT 1
                                FROM group_classes
                                WHERE room_id = %s
                                  AND class_date = %s
                                  AND %s < end_time
                                  AND %s > start_time
                                  AND class_id <> %s
                                UNION ALL
                                SELECT 1
                                FROM personal_training_sessions
                                WHERE room_id = %s
                                  AND session_date = %s
                                  AND %s < end_time
                                  AND %s > start_time
                                LIMIT 1
                                """,
                                (
                                    room_id,
                                    booking['booking_date'],
                                    booking['start_time'],
                                    booking['end_time'],
                                    booking['booking_id'],
                                    room_id,
                                    booking['booking_date'],
                                    booking['start_time'],
                                    booking['end_time'],
                                ),
                            )
                            if cur.fetchone():
                                flash('Room already booked at that time.', 'error')
                            else:
                                cur.execute(
                                    """
                                    UPDATE group_classes
                                    SET room_id = %s
                                    WHERE class_id = %s
                                    """,
                                    (room_id, booking_id),
                                )
                                conn.commit()
                                flash('Room assignment updated successfully.', 'success')
                    else:
                        flash('Invalid booking type selected.', 'error')
            except Exception:
                conn.rollback()
                flash('Unable to update room booking right now.', 'error')

        with conn.cursor() as cur:
            cur.execute(
                'SELECT room_id, room_name, capacity, location FROM rooms ORDER BY room_name ASC'
            )
            rooms = cur.fetchall()

            cur.execute(
                """
                SELECT pts.session_id, pts.session_date, pts.start_time, pts.end_time,
                       m.full_name AS member_name,
                       t.full_name AS trainer_name,
                       COALESCE(r.room_name, 'Unassigned') AS room_name,
                       pts.room_id
                FROM personal_training_sessions pts
                JOIN members m ON m.member_id = pts.member_id
                JOIN trainers t ON t.trainer_id = pts.trainer_id
                LEFT JOIN rooms r ON r.room_id = pts.room_id
                ORDER BY pts.session_date ASC, pts.start_time ASC
                """
            )
            personal_sessions = cur.fetchall()

            cur.execute(
                """
                SELECT gc.class_id, gc.class_name, gc.class_date, gc.start_time, gc.end_time,
                       t.full_name AS trainer_name,
                       COALESCE(r.room_name, 'Unassigned') AS room_name,
                       gc.room_id
                FROM group_classes gc
                JOIN trainers t ON t.trainer_id = gc.trainer_id
                LEFT JOIN rooms r ON r.room_id = gc.room_id
                ORDER BY gc.class_date ASC, gc.start_time ASC
                """
            )
            group_classes = cur.fetchall()

        return render_template(
            'admin/room_booking.html',
            rooms=rooms,
            personal_sessions=personal_sessions,
            group_classes=group_classes,
        )
    except Exception:
        flash('Unable to load room booking information.', 'error')
        return render_template(
            'admin/room_booking.html',
            rooms=[],
            personal_sessions=[],
            group_classes=[],
        )
    finally:
        if conn:
            conn.close()


@app.route('/admin/equipment', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_equipment():
    equipment_items = []
    rooms = []
    filter_mode = request.args.get('filter', 'all')
    conn = None

    try:
        conn = get_db_connection()

        if request.method == 'POST':
            action = request.form.get('action', '').strip()
            try:
                with conn.cursor() as cur:
                    if action == 'log_issue':
                        name = request.form.get('name', '').strip()
                        room_id = request.form.get('room_id', '').strip()
                        if not name or not room_id:
                            flash('Equipment name and room are required.', 'error')
                        else:
                            cur.execute(
                                """
                                INSERT INTO equipment (name, room_id, status)
                                VALUES (%s, %s, 'under repair')
                                """,
                                (name, room_id),
                            )
                            conn.commit()
                            flash('Maintenance issue logged successfully.', 'success')
                    elif action == 'update_status':
                        equipment_id = request.form.get('equipment_id', '').strip()
                        status = request.form.get('status', '').strip()
                        valid_statuses = {'operational', 'under repair', 'out of service'}
                        if status not in valid_statuses:
                            flash('Invalid equipment status selected.', 'error')
                        else:
                            cur.execute(
                                """
                                UPDATE equipment
                                SET status = %s, last_updated = CURRENT_TIMESTAMP
                                WHERE equipment_id = %s
                                """,
                                (status, equipment_id),
                            )
                            conn.commit()
                            if cur.rowcount:
                                flash('Equipment status updated successfully.', 'success')
                            else:
                                flash('Equipment item not found.', 'error')
                    else:
                        flash('Invalid request.', 'error')
            except Exception:
                conn.rollback()
                flash('Unable to update equipment right now.', 'error')

        with conn.cursor() as cur:
            cur.execute('SELECT room_id, room_name, location FROM rooms ORDER BY room_name ASC')
            rooms = cur.fetchall()

            if filter_mode == 'non_operational':
                cur.execute(
                    """
                    SELECT e.equipment_id, e.name, e.status, e.last_updated,
                           r.room_name, r.location
                    FROM equipment e
                    JOIN rooms r ON r.room_id = e.room_id
                    WHERE e.status <> 'operational'
                    ORDER BY e.last_updated DESC, e.name ASC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT e.equipment_id, e.name, e.status, e.last_updated,
                           r.room_name, r.location
                    FROM equipment e
                    JOIN rooms r ON r.room_id = e.room_id
                    ORDER BY e.last_updated DESC, e.name ASC
                    """
                )
            equipment_items = cur.fetchall()
    except Exception:
        flash('Unable to load equipment information.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template(
        'admin/equipment.html',
        equipment_items=equipment_items,
        rooms=rooms,
        filter_mode=filter_mode,
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
