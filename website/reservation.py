import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import calendar
import json
from .models import Notification, get_db_connection, OwnerCottage, Amenity
from .models import OwnerNotification

reservation_bp = Blueprint('reservation', __name__)

@reservation_bp.route('/owner-reservations')
@login_required
def owner_reservations():
    """
    Display all reservations for cottages owned by the current user
    """
    if current_user.role != 'owner':
        flash('Access denied. Owner privileges required.', 'error')
        return redirect(url_for('views.home'))
        
    conn = get_db_connection()
    try:
        
        user_cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
        
        # Get pending reservations
        pending_reservations = []
        cottage_ids = [cottage.id for cottage in user_cottages]
        
        if cottage_ids:
            placeholders = ','.join('?' * len(cottage_ids))
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT r.*, 
                       u.name as guest_name, 
                       u.email as guest_email, 
                       u.phone as guest_phone,
                       oc.cottage_no,
                       oc.cottage_location,
                       oc.cottage_image,
                       t.table_no
                FROM reservations r
                INNER JOIN users u ON r.user_id = u.id
                INNER JOIN owner_cottages oc ON r.cottage_id = oc.id
                LEFT JOIN cottage_tables t ON r.table_id = t.id
                WHERE r.cottage_id IN ({placeholders})
                AND r.cottage_status = 'pending'
                ORDER BY r.date_stay ASC
            ''', cottage_ids)
            
            pending_reservations = cursor.fetchall()
        
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get active reservations for today
        active_today = []
        if cottage_ids:
            placeholders = ','.join('?' * len(cottage_ids))
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT r.*, 
                       u.name as guest_name, 
                       u.email as guest_email, 
                       u.phone as guest_phone,
                       oc.cottage_no,
                       oc.cottage_location,
                       oc.cottage_image,
                       t.table_no
                FROM reservations r
                INNER JOIN users u ON r.user_id = u.id
                INNER JOIN owner_cottages oc ON r.cottage_id = oc.id
                LEFT JOIN cottage_tables t ON r.table_id = t.id
                WHERE r.cottage_id IN ({placeholders})
                AND r.cottage_status IN ('reserved', 'approved')
                AND r.date_stay = ?
                ORDER BY r.start_time ASC
            ''', cottage_ids + [today])
            
            active_today = cursor.fetchall()
        
        # Get upcoming reservations (excluding today)
        upcoming_reservations = []
        if cottage_ids:
            placeholders = ','.join('?' * len(cottage_ids))
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT r.*, 
                       u.name as guest_name, 
                       u.email as guest_email, 
                       u.phone as guest_phone,
                       oc.cottage_no,
                       oc.cottage_location,
                       oc.cottage_image,
                       t.table_no,
                       julianday(r.date_stay) - julianday(?) as days_until
                FROM reservations r
                INNER JOIN users u ON r.user_id = u.id
                INNER JOIN owner_cottages oc ON r.cottage_id = oc.id
                LEFT JOIN cottage_tables t ON r.table_id = t.id
                WHERE r.cottage_id IN ({placeholders})
                AND r.cottage_status IN ('reserved', 'approved')
                AND r.date_stay > ?
                ORDER BY r.date_stay ASC
            ''', [today] + cottage_ids + [today])
            
            upcoming_reservations = cursor.fetchall()
        
        # Get unread notifications count
        from .models import Notification
        unread_notifications = Notification.get_unread_count(conn, current_user.id)
        
        return render_template('owner_reservations.html', 
                              pending_reservations=pending_reservations,
                              active_today=active_today,
                              upcoming_reservations=upcoming_reservations,
                              now=today,
                              tomorrow=tomorrow,
                              unread_notifications=unread_notifications,
                              user=current_user)
    finally:
        conn.close()

@reservation_bp.route('/cottage-availability-calendar')
@login_required
def cottage_availability_calendar():
    """
    Display a calendar view of cottage availability for owners
    """
    if current_user.role != 'owner':
        flash('Access denied. Owner privileges required.', 'error')
        return redirect(url_for('views.home'))
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        
        cursor.execute('''
            SELECT * FROM owner_cottages 
            WHERE user_id = ?
        ''', (current_user.id,))
        cottages = cursor.fetchall()
        
        # Default to current month and year if not specified
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Set selected cottage if provided in query parameters
        selected_cottage_id = request.args.get('cottage_id', None, type=int)
        if selected_cottage_id:
            cursor.execute('SELECT * FROM owner_cottages WHERE id = ? AND user_id = ?', 
                          (selected_cottage_id, current_user.id))
            selected_cottage = cursor.fetchone()
        else:
            selected_cottage = cottages[0] if cottages else None
        
        # Get calendar data
        cal_data = None
        reserved_dates = []
        
        if selected_cottage:
            # Get all reservations for the selected cottage in the specified month
            cursor.execute('''
                SELECT date_stay, cottage_status, start_time, end_time 
                FROM reservations 
                WHERE cottage_id = ? 
                AND strftime('%Y-%m', date_stay) = ?
                AND cottage_status IN ('reserved', 'approved')
            ''', (selected_cottage['id'], f"{year}-{month:02d}"))
            
            reservations = cursor.fetchall()
            
            # Format the calendar data
            cal = calendar.monthcalendar(year, month)
            cal_data = []
            
            for week in cal:
                week_data = []
                for day in week:
                    if day == 0:
                        # Padding for days not in this month
                        week_data.append({
                            'day': '',
                            'status': 'inactive',
                            'reservations': []
                        })



                    else:
                        day_reservations = []
                        day_status = 'available'
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        
                        # Check if this day has any reservations
                        for res in reservations:
                            if res['date_stay'] == date_str:
                                status_label = 'Pending' if res['cottage_status'] == 'reserved' else 'Confirmed'
                                day_reservations.append({
                                    'time': f"{res['start_time']} - {res['end_time']}",
                                    'status': res['cottage_status'],
                                    'status_label': status_label
                                })
                                day_status = 'reserved'
                                reserved_dates.append(date_str)
                        
                        week_data.append({
                            'day': day,
                            'date': date_str,
                            'status': day_status,
                            'reservations': day_reservations
                        })
                cal_data.append(week_data)
        
        # Prepare month navigation data
        current_date = datetime(year, month, 1)
        prev_month = (current_date - timedelta(days=1)).replace(day=1)
        next_month = (current_date + timedelta(days=32)).replace(day=1)
        
        month_nav = {
            'current': {
                'month': month,
                'year': year,
                'name': current_date.strftime('%B %Y')
            },
            'prev': {
                'month': prev_month.month,
                'year': prev_month.year,
                'name': prev_month.strftime('%B %Y')
            },
            'next': {
                'month': next_month.month,
                'year': next_month.year,
                'name': next_month.strftime('%B %Y')
            }
        }
        
        return render_template('cottage_calendar.html',
                              cottages=cottages,
                              selected_cottage=selected_cottage,
                              calendar=cal_data,
                              month_nav=month_nav,
                              reserved_dates=json.dumps(reserved_dates))
    finally:
        conn.close()

@reservation_bp.route('/api/cottage-availability/<int:cottage_id>')
@login_required
def api_cottage_availability(cottage_id):
    """
    API endpoint to get cottage availability dates
    """
    if current_user.role != 'owner':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify ownership of the cottage
        cursor.execute('SELECT * FROM owner_cottages1 WHERE id = ? AND user_id = ?', 
                      (cottage_id, current_user.id))
        cottage = cursor.fetchone()
        
        if not cottage:
            return jsonify({'error': 'Cottage not found or access denied'}), 404
        
        # Get the date range from query parameters
        start_date = request.args.get('start', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('end', (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'))
        
        # Get all reservations for this cottage within the date range
        cursor.execute('''
            SELECT id, date_stay, start_time, end_time, cottage_status, user_id
            FROM reservations
            WHERE cottage_id = ?
            AND date_stay BETWEEN ? AND ?
            AND cottage_status IN ('reserved', 'approved')
        ''', (cottage_id, start_date, end_date))
        
        reservations = cursor.fetchall()
        
        # Get user information for each reservation
        availability_data = []
        for res in reservations:
            cursor.execute('SELECT name, email, phone FROM users WHERE id = ?', (res['user_id'],))
            user = cursor.fetchone()
            
            status_color = 'yellow' if res['cottage_status'] == 'reserved' else 'red'
            status_text = 'Pending Approval' if res['cottage_status'] == 'reserved' else 'Reserved'
            
            availability_data.append({
                'id': res['id'],
                'date': res['date_stay'],
                'time': f"{res['start_time']} - {res['end_time']}",
                'status': res['cottage_status'],
                'status_color': status_color,
                'status_text': status_text,
                'guest': user['name'] if user else 'Unknown',
                'contact': user['phone'] if user else 'N/A',
                'email': user['email'] if user else 'N/A'
            })
        
        return jsonify({
            'cottage': {
                'id': cottage['id'],
                'name': cottage['cottage_no'],
                'location': cottage['cottage_location']
            },
            'reservations': availability_data
        })
    finally:
        conn.close()

@reservation_bp.route('/process_reservation', methods=['POST'])
@login_required
def process_reservation():
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            cottage_id = request.form.get('cottage_id')
            date_stay = request.form.get('date_stay')
            max_persons = request.form.get('max_persons')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            amount = request.form.get('amount')
            
            # Validate required fields
            if not cottage_id or not date_stay or not max_persons or not start_time or not end_time or not amount:
                flash('Please fill all required fields', 'error')
                return redirect(url_for('views.make_reservation'))
            
            # Convert to appropriate data types
            cottage_id = int(cottage_id)
            max_persons = int(max_persons)
            amount = float(amount)
            
            # Get cottage information
            cursor = conn.cursor()
            # Fixed: Changed table name from owner_cottages1 to owner_cottages
            cursor.execute('SELECT * FROM owner_cottages WHERE id = ?', (cottage_id,))
            cottage_data = cursor.fetchone()
            
            if not cottage_data:
                flash('Selected cottage not found', 'error')
                return redirect(url_for('views.make_reservation'))
            
            # Validate max persons
            if max_persons > cottage_data['max_persons']:
                flash(f'Maximum number of persons for this cottage is {cottage_data["max_persons"]}', 'error')
                return redirect(url_for('views.make_reservation'))
            
            # Check for conflicting reservations
            from .models import Reservation as ReservationModel
            conflicting_reservations = ReservationModel.find_conflicting_reservations(
                conn, cottage_id, date_stay, start_time, end_time
            )
            
            if conflicting_reservations:
                flash('This cottage is already reserved for the selected date and time. Please choose another date/time or cottage.', 'error')
                return redirect(url_for('views.make_reservation'))
            
            # Process selected amenities
            selected_amenities = request.form.getlist('amenities')
            amenities_id = ','.join(selected_amenities) if selected_amenities else None
            
            # Create new reservation
            new_reservation = ReservationModel(
                user_id=current_user.id,
                cottage_id=cottage_id,
                amenities_id=amenities_id,
                max_persons=max_persons,
                date_stay=date_stay,
                start_time=start_time,
                end_time=end_time,
                amount=amount,
                cottage_status="pending",  # Fixed: Changed from "reserved" to "pending" to match workflow
                date_reserved=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Save reservation to database
            reservation_id = new_reservation.save_to_db(conn)
            
            # Create notifications for both the owner and user
            from .models import Notification
            Notification.create_reservation_notification(conn, reservation_id)
            
            # Success message
            flash('Reservation successfully created! Your request is now pending approval.', 'success')
            return redirect(url_for('views.make_reservation'))
        except Exception as e:
            conn.rollback()
            flash(f'Error creating reservation: {str(e)}', 'error')
            return redirect(url_for('views.make_reservation'))
        finally:
            conn.close()
    
    # If not POST request
    return redirect(url_for('views.make_reservation'))

@reservation_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    """Allow a user to cancel their reservation"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify this reservation belongs to the current user and is still pending or reserved
        cursor.execute("""
            SELECT id, cottage_status
            FROM reservations
            WHERE id = ? AND user_id = ? AND cottage_status IN ('pending', 'reserved')
        """, (reservation_id, current_user.id))
        
        reservation = cursor.fetchone()
        if not reservation:
            flash('Invalid reservation or not authorized to cancel.', 'error')
            return redirect(url_for('reservation.view_my_reservations'))
        
        # Update reservation status
        cursor.execute("""
            UPDATE reservations
            SET cottage_status = 'cancelled'
            WHERE id = ?
        """, (reservation_id,))
        
        # Create notification for the owner
        Notification.create_owner_cancellation_notification(conn, reservation_id)
        
        conn.commit()
        flash('Reservation cancelled successfully.', 'success')
        return redirect(url_for('reservation.view_my_reservations'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Error cancelling reservation: {str(e)}', 'error')
        return redirect(url_for('reservation.view_my_reservations'))
    finally:
        conn.close()

@reservation_bp.route('/approve_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def approve_reservation(reservation_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.* FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ? AND oc.user_id = ?
        ''', (reservation_id, current_user.id))
        reservation = cursor.fetchone()
        
        if not reservation:
            flash('Reservation not found or you do not have permission to approve it.', 'error')
            return redirect(url_for('reservation.owner_reservations'))
        
        # Use a try-except block to catch the SQLite3 error if the database is locked
        try:
            cursor.execute('UPDATE reservations SET cottage_status = ? WHERE id = ?',
                          ('approved', reservation_id))
            conn.commit()
        except sqlite3.Error as e:
            if 'database is locked' in str(e):
                flash('Database is locked. Please try again later.')
                return redirect(url_for('reservation.owner_reservations'))
        
        from .models import Notification, OwnerNotification
        
        # Create notification for the guest
        Notification.create_approval_notification(conn, reservation_id)
        
        # Create notification for the owner's records
        OwnerNotification.create_approval_notification(conn, reservation_id)
        
        flash('Reservation has been approved.', 'success')
        return redirect(url_for('reservation.owner_reservations'))
    finally:
        conn.close()
        
@reservation_bp.route('/decline_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def decline_reservation(reservation_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        #
        cursor.execute('''
            SELECT r.* FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ? AND oc.user_id = ?
        ''', (reservation_id, current_user.id))
        reservation = cursor.fetchone()
        
        if not reservation:
            flash('Reservation not found or you do not have permission to decline it.', 'error')
            return redirect(url_for('reservation.owner_reservations'))
        # Use a try-except block to catch the SQLite3 error if the database is locked
        try:
            cursor.execute('UPDATE reservations SET cottage_status = ? WHERE id = ?', 
                          ('declined', reservation_id))
            conn.commit()
        except sqlite3.Error as e:
            if 'database is locked' in str(e):
                flash('Database is locked. Please try again later.')
                return redirect(url_for('reservation.owner_reservations'))
        
        # Create notification for the guest
        Notification.create_decline_notification(conn, reservation_id)
        
        # Create notification for the owner's records
        OwnerNotification.create_decline_notification(conn, reservation_id)
        
        flash('Reservation has been declined.', 'success')
        return redirect(url_for('reservation.owner_reservations'))
    finally:
        conn.close()

@reservation_bp.route('/user-notifications')
@login_required
def notifications():
    conn = get_db_connection()
    try:
        from .models import Notification
        notifications = Notification.get_user_notifications(conn, current_user.id)
        
        return render_template('notifications.html', notifications=notifications)
    finally:
        conn.close()

@reservation_bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    conn = get_db_connection()
    try:
        from .models import Notification
        success = Notification.mark_as_read(conn, notification_id, current_user.id)
        
        return {'success': success}
    finally:
        conn.close()

@reservation_bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    conn = get_db_connection()
    try:
        from .models import Notification
        count = Notification.mark_all_as_read(conn, current_user.id)
        
        return {'success': True, 'count': count}
    finally:
        conn.close()

@reservation_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    conn = get_db_connection()
    try:
        from .models import Notification
        success = Notification.delete_notification(conn, notification_id, current_user.id)
        
        return {'success': success}
    finally:
        conn.close()

@reservation_bp.route('/notifications/delete_all', methods=['POST'])
@login_required
def delete_all_notifications():
    conn = get_db_connection()
    try:
        from .models import Notification
        count = Notification.delete_all_notifications(conn, current_user.id)
        
        return {'success': True, 'count': count}
    finally:
        conn.close()

@reservation_bp.route('/notifications/filter')
@login_required
def filter_notifications():
    conn = get_db_connection()
    try:
        from .models import Notification
        
        notification_type = request.args.get('type', 'all')
        status = request.args.get('status', 'all')
        
        filtered_notifications = Notification.filter_notifications(
            conn, current_user.id, notification_type, status
        )
        
        notifications_dict = [notification.to_dict() for notification in filtered_notifications]
        
        return {'success': True, 'notifications': notifications_dict}
    finally:
        conn.close()

