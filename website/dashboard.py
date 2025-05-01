from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import get_db_connection, OwnerCottage, CottageTable, Reservation, Notification, User, OwnerNotification

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def dashboard_view():
    """Display the main dashboard with summary of cottages and reservations"""
    conn = get_db_connection()
    
    # Get user's cottages if they are an owner
    user_cottages = []
    if current_user.role == 'owner':
        user_cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
    
    # Get user's reservations
    user_reservations = Reservation.get_reservations_by_user_id(conn, current_user.id)
    
    # Get notification count
    unread_notifications = OwnerNotification.get_unread_count(conn, current_user.id)
    
    # Get pending reservations (for owners)
    pending_reservations = []
    if current_user.role == 'owner':
        for cottage in user_cottages:
            cursor = conn.execute('''
                SELECT r.*, u.name as customer_name, u.email as customer_email,
                       oc.cottage_no, ct.table_no
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN owner_cottages oc ON r.cottage_id = oc.id
                LEFT JOIN cottage_tables ct ON r.table_id = ct.id
                WHERE r.cottage_id = ? AND r.cottage_status = 'pending'
                ORDER BY r.date_stay ASC
            ''', (cottage.id,))
            pending_reservations.extend(cursor.fetchall())
    
    # Get today's date
    today_date = datetime.now()
    today = today_date.strftime('%Y-%m-%d')  # for SQL queries
    formatted_today = today_date.strftime('%B %d %Y')  # for display
    
    # Get today's reservations
    todays_reservations = []
    if current_user.role == 'owner':
        if user_cottages:
            cottage_ids = [c.id for c in user_cottages]
            placeholders = ','.join('?' * len(cottage_ids))
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT r.*, 
                       u.name as customer_name,
                       u.email as customer_email, 
                       u.phone as customer_phone,
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
            
            todays_reservations = cursor.fetchall()
    else:
        cursor = conn.execute('''
            SELECT r.*, 
                   oc.cottage_no, 
                   oc.cottage_location,
                   oc.cottage_image,
                   u.name as owner_name, 
                   t.table_no
            FROM reservations r
            INNER JOIN owner_cottages oc ON r.cottage_id = oc.id
            INNER JOIN users u ON oc.user_id = u.id
            LEFT JOIN cottage_tables t ON r.table_id = t.id
            WHERE r.user_id = ?
            AND r.cottage_status IN ('reserved', 'approved')
            AND r.date_stay = ?
            ORDER BY r.start_time ASC
        ''', (current_user.id, today))
        
        todays_reservations = cursor.fetchall()
    
    # Get upcoming reservations (excluding today)
    upcoming_reservations = []
    if current_user.role == 'owner':
        if user_cottages:
            cottage_ids = [c.id for c in user_cottages]
            placeholders = ','.join('?' * len(cottage_ids))
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT r.*, 
                       u.name as customer_name,  
                       u.email as customer_email, 
                       u.phone as customer_phone,
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
                LIMIT 5
            ''', [today] + cottage_ids + [today])
            
            upcoming_reservations = cursor.fetchall()
    else:
        cursor = conn.execute('''
            SELECT r.*, 
                   oc.cottage_no, 
                   oc.cottage_location,
                   oc.cottage_image,
                   u.name as owner_name, 
                   t.table_no,
                   julianday(r.date_stay) - julianday(?) as days_until
            FROM reservations r
            INNER JOIN owner_cottages oc ON r.cottage_id = oc.id
            INNER JOIN users u ON oc.user_id = u.id
            LEFT JOIN cottage_tables t ON r.table_id = t.id
            WHERE r.user_id = ?
            AND r.cottage_status IN ('reserved', 'approved')
            AND r.date_stay > ?
            ORDER BY r.date_stay ASC
            LIMIT 5
        ''', (today, current_user.id, today))
        
        upcoming_reservations = cursor.fetchall()
    
    # Calculate stats for owners
    stats = {}
    if current_user.role == 'owner':
        stats['total_cottages'] = len(user_cottages)
        
        cursor = conn.execute('''
            SELECT COUNT(*) as count FROM cottage_tables ct
            JOIN owner_cottages oc ON ct.cottage_id = oc.id
            WHERE oc.user_id = ?
        ''', (current_user.id,))
        stats['total_tables'] = cursor.fetchone()['count']
        
        cottage_ids = [c.id for c in user_cottages]
        if cottage_ids:
            placeholders = ','.join('?' * len(cottage_ids))
            query = f'SELECT COUNT(*) as count FROM reservations WHERE cottage_id IN ({placeholders})'
            cursor = conn.execute(query, cottage_ids)
            stats['total_reservations'] = cursor.fetchone()['count']
        else:
            stats['total_reservations'] = 0
        
        first_day = datetime.now().replace(day=1).strftime('%B %d %Y')
        last_day = (datetime.now().replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        last_day = last_day.strftime('%Y-%m-%d')
        
        if cottage_ids:
            placeholders = ','.join('?' * len(cottage_ids))
            query = f'''
                SELECT SUM(amount) as total FROM reservations 
                WHERE cottage_id IN ({placeholders}) 
                AND date_stay BETWEEN ? AND ?
                AND cottage_status = 'reserved'
            '''
            params = cottage_ids + [first_day, last_day]
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
            stats['monthly_revenue'] = result['total'] if result and result['total'] else 0
        else:
            stats['monthly_revenue'] = 0
    
    conn.close()
    
    return render_template('dashboard.html', 
                           cottages=user_cottages,
                           reservations=user_reservations,
                           pending_reservations=pending_reservations,
                           upcoming_reservations=upcoming_reservations,
                           todays_reservations=todays_reservations,
                           unread_notifications=unread_notifications,
                           stats=stats,
                           user=current_user,
                           today=today,
                           formatted_today=formatted_today)

@dashboard.route('/dashboard/reservations')
@login_required
def reservations():
    """View all reservations"""
    conn = get_db_connection()
    user_reservations = []
    
    if current_user.role == 'user':
        # For regular users, show their reservations
        cursor = conn.execute('''
            SELECT r.*, oc.cottage_no, oc.owner_name, 
                   ct.table_no, ct.capacity, 
                   u.name as owner_name
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            LEFT JOIN cottage_tables ct ON r.table_id = ct.id
            JOIN users u ON oc.user_id = u.id
            WHERE r.user_id = ?
            ORDER BY r.date_stay DESC
        ''', (current_user.id,))
        user_reservations = cursor.fetchall()
    else:
        # For owners, show reservations for their cottages
        cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
        cottage_ids = [c.id for c in cottages]
        
        if cottage_ids:
            placeholders = ','.join('?' * len(cottage_ids))
            query = f'''
                SELECT r.*, u.name as customer_name, u.email as customer_email,
                       oc.cottage_no, ct.table_no, ct.capacity
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN owner_cottages oc ON r.cottage_id = oc.id
                LEFT JOIN cottage_tables ct ON r.table_id = ct.id
                WHERE r.cottage_id IN ({placeholders})
                ORDER BY r.date_stay DESC
            '''
            cursor = conn.execute(query, cottage_ids)
            user_reservations = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard/reservations.html', 
                          reservations=user_reservations)

@dashboard.route('/dashboard/pending_reservations')
@login_required
def pending_reservations():
    """View pending reservations (for cottage owners)"""
    if current_user.role != 'owner':
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    conn = get_db_connection()
    cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
    
    pending_reservations = []
    for cottage in cottages:
        cursor = conn.execute('''
            SELECT r.*, u.name as customer_name, u.email as customer_email,
                   u.username as customer_username,
                   oc.cottage_no, oc.cottage_location,
                   ct.table_no, ct.capacity
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            LEFT JOIN cottage_tables ct ON r.table_id = ct.id
            WHERE r.cottage_id = ? AND r.cottage_status = 'pending'
            ORDER BY r.date_stay ASC
        ''', (cottage.id,))
        pending_reservations.extend(cursor.fetchall())
    
    conn.close()
    
    return redirect(url_for('reservation.owner_reservations'))

@dashboard.route('/dashboard/approve_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def approve_reservation(reservation_id):
    """Approve a pending reservation"""
    if current_user.role != 'owner':
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    conn = get_db_connection()
    
    # Verify the reservation is for one of the user's cottages
    cursor = conn.execute('''
        SELECT r.*, oc.user_id as cottage_owner_id, u.name as customer_name
        FROM reservations r
        JOIN owner_cottages oc ON r.cottage_id = oc.id
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
    ''', (reservation_id,))
    
    reservation = cursor.fetchone()
    
    if not reservation:
        flash('Reservation not found', 'danger')
        conn.close()
        return redirect(url_for('reservation.owner_reservations'))
    
    if reservation['cottage_owner_id'] != current_user.id:
        flash('You do not have permission to approve this reservation', 'danger')
        conn.close()
        return redirect(url_for('reservation.owner_reservations'))
    
    # Update reservation status
    conn.execute('''
        UPDATE reservations
        SET cottage_status = 'reserved'
        WHERE id = ?
    ''', (reservation_id,))
    
    # Create notification for the customer
    now = datetime.now()
    notification = Notification(
        user_id=reservation['user_id'],
        message=f"Your reservation for {reservation['date_stay']} has been approved!",
        notification_type='reservation',
        related_id=reservation_id,
        created_at=now,
        read=False
    )
    notification.save_to_db(conn)
    
    conn.commit()
    conn.close()
    
    flash(f"Reservation for {reservation['customer_name']} has been approved", 'success')
    return redirect(url_for('reservation.owner_reservations'))

@dashboard.route('/dashboard/reject_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def reject_reservation(reservation_id):
    """Reject a pending reservation"""
    if current_user.role != 'owner':
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    reason = request.form.get('reason', 'No reason provided')
    
    conn = get_db_connection()
    
    # Verify the reservation is for one of the user's cottages
    cursor = conn.execute('''
        SELECT r.*, oc.user_id as cottage_owner_id, u.name as customer_name
        FROM reservations r
        JOIN owner_cottages oc ON r.cottage_id = oc.id
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
    ''', (reservation_id,))
    
    reservation = cursor.fetchone()
    
    if not reservation:
        flash('Reservation not found', 'danger')
        conn.close()
        return redirect(url_for('dashboard.pending_reservations'))
    
    if reservation['cottage_owner_id'] != current_user.id:
        flash('You do not have permission to reject this reservation', 'danger')
        conn.close()
        return redirect(url_for('dashboard.pending_reservations'))
    
    # Update reservation status
    conn.execute('''
        UPDATE reservations
        SET cottage_status = 'rejected'
        WHERE id = ?
    ''', (reservation_id,))
    
    # Create notification for the customer
    now = datetime.now()
    notification = Notification(
        user_id=reservation['user_id'],
        message=f"Your reservation for {reservation['date_stay']} has been rejected. Reason: {reason}",
        notification_type='reservation',
        related_id=reservation_id,
        created_at=now,
        read=False
    )
    notification.save_to_db(conn)
    
    conn.commit()
    conn.close()
    
    flash(f"Reservation for {reservation['customer_name']} has been rejected", 'warning')
    return redirect(url_for('dashboard.dashboard'))

@dashboard.route('/dashboard/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    """Cancel a reservation"""
    conn = get_db_connection()
    
    # Verify the reservation belongs to the current user or their cottage
    if current_user.role == 'user':
        cursor = conn.execute('''
            SELECT r.*, oc.cottage_no, u.name as owner_name
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN users u ON oc.user_id = u.id
            WHERE r.id = ? AND r.user_id = ?
        ''', (reservation_id, current_user.id))
    else:
        cursor = conn.execute('''
            SELECT r.*, oc.cottage_no, u.name as customer_name, u.id as customer_id
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ? AND oc.user_id = ?
        ''', (reservation_id, current_user.id))
    
    reservation = cursor.fetchone()
    
    if not reservation:
        flash('Reservation not found or you do not have permission to cancel it', 'danger')
        conn.close()
        return redirect(url_for('dashboard.dashboard'))
    
    # Update reservation status
    conn.execute('''
        UPDATE reservations
        SET cottage_status = 'cancelled'
        WHERE id = ?
    ''', (reservation_id,))
    
    # Create notification for the other party
    now = datetime.now()
    
    if current_user.role == 'user':
        # Get cottage owner's ID
        cursor = conn.execute('''
            SELECT oc.user_id FROM owner_cottages oc
            WHERE oc.id = ?
        ''', (reservation['cottage_id'],))
        owner_data = cursor.fetchone()
        
        if owner_data:
            notification = Notification(
                user_id=owner_data['user_id'],
                message=f"Reservation for {reservation['date_stay']} has been cancelled by the customer.",
                notification_type='reservation',
                related_id=reservation_id,
                created_at=now,
                read=False
            )
            notification.save_to_db(conn)
    else:
        # Notification for the customer
        notification = Notification(
            user_id=reservation['customer_id'],
            message=f"Your reservation for {reservation['date_stay']} has been cancelled by the owner.",
            notification_type='reservation',
            related_id=reservation_id,
            created_at=now,
            read=False
        )
        notification.save_to_db(conn)
    
    conn.commit()
    conn.close()
    
    flash("Reservation has been cancelled", 'warning')
    return redirect(url_for('dashboard.reservations'))

@dashboard.route('/dashboard/tables')
@login_required
def tables():
    """View all tables for owner's cottages"""
    if current_user.role != 'owner':
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    conn = get_db_connection()
    cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
    
    cottage_tables = {}
    for cottage in cottages:
        tables = CottageTable.get_by_cottage_id(conn, cottage.id)
        cottage_tables[cottage.id] = {
            'cottage': cottage,
            'tables': tables
        }
    
    conn.close()
    
    return render_template('dashboard/tables.html', 
                          cottage_tables=cottage_tables)

@dashboard.route('/dashboard/table_reservations/<int:table_id>')
@login_required
def table_reservations(table_id):
    """View reservations for a specific table"""
    if current_user.role != 'owner':
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    conn = get_db_connection()
    
    # Verify the table belongs to one of the user's cottages
    cursor = conn.execute('''
        SELECT ct.*, oc.cottage_no, oc.user_id as cottage_owner_id
        FROM cottage_tables ct
        JOIN owner_cottages oc ON ct.cottage_id = oc.id
        WHERE ct.id = ?
    ''', (table_id,))
    
    table = cursor.fetchone()
    
    if not table or table['cottage_owner_id'] != current_user.id:
        flash('Table not found or you do not have permission to view it', 'danger')
        conn.close()
        return redirect(url_for('dashboard.tables'))
    
    # Get reservations for this table
    cursor = conn.execute('''
        SELECT r.*, u.name as customer_name, u.email as customer_email
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        WHERE r.table_id = ?
        ORDER BY r.date_stay DESC
    ''', (table_id,))
    
    table_reservations = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard/table_reservations.html', 
                          table=table,
                          reservations=table_reservations)

@dashboard.route('/dashboard/analytics')
@login_required
def analytics():
    """Show analytics and insights for cottage owners"""
    if current_user.role != 'owner':
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    conn = get_db_connection()
    cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
    cottage_ids = [c.id for c in cottages]
    
    # Initialize analytics data
    analytics_data = {
        'total_reservations': 0,
        'total_revenue': 0,
        'reservation_status': {
            'pending': 0,
            'reserved': 0,
            'cancelled': 0,
            'rejected': 0
        },
        'monthly_revenue': [],
        'cottage_performance': []
    }
    
    if cottage_ids:
        placeholders = ','.join('?' * len(cottage_ids))
        
        # Total reservations and revenue
        query = f'''
            SELECT COUNT(*) as count, SUM(amount) as total
            FROM reservations
            WHERE cottage_id IN ({placeholders})
        '''
        cursor = conn.execute(query, cottage_ids)
        result = cursor.fetchone()
        
        if result:
            analytics_data['total_reservations'] = result['count']
            analytics_data['total_revenue'] = result['total'] or 0
        
        # Reservation status counts
        query = f'''
            SELECT cottage_status, COUNT(*) as count
            FROM reservations
            WHERE cottage_id IN ({placeholders})
            GROUP BY cottage_status
        '''
        cursor = conn.execute(query, cottage_ids)
        
        for row in cursor.fetchall():
            status = row['cottage_status']
            if status in analytics_data['reservation_status']:
                analytics_data['reservation_status'][status] = row['count']
        
        # Monthly revenue for the past 6 months
        months = []
        for i in range(5, -1, -1):
            date = datetime.now() - timedelta(days=30*i)
            first_day = date.replace(day=1).strftime('%Y-%m-%d')
            last_day = (date.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            last_day = last_day.strftime('%Y-%m-%d')
            months.append((date.strftime('%B %Y'), first_day, last_day))
        
        for month_name, first_day, last_day in months:
            query = f'''
                SELECT SUM(amount) as total
                FROM reservations
                WHERE cottage_id IN ({placeholders})
                AND date_stay BETWEEN ? AND ?
                AND cottage_status = 'reserved'
            '''
            params = cottage_ids + [first_day, last_day]
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
            
            analytics_data['monthly_revenue'].append({
                'month': month_name,
                'revenue': result['total'] if result and result['total'] else 0
            })
        
        # Cottage performance
        for cottage in cottages:
            # Reservations count
            cursor = conn.execute('''
                SELECT COUNT(*) as count
                FROM reservations
                WHERE cottage_id = ? AND cottage_status = 'reserved'
            ''', (cottage.id,))
            reservations_count = cursor.fetchone()['count']
            
            # Revenue
            cursor = conn.execute('''
                SELECT SUM(amount) as total
                FROM reservations
                WHERE cottage_id = ? AND cottage_status = 'reserved'
            ''', (cottage.id,))
            revenue = cursor.fetchone()['total'] or 0
            
            analytics_data['cottage_performance'].append({
                'cottage_id': cottage.id,
                'cottage_no': cottage.cottage_no,
                'reservations': reservations_count,
                'revenue': revenue
            })
    
    conn.close()
    
    return render_template('dashboard/analytics.html', 
                          analytics=analytics_data)