from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from . import get_db_connection
from .models import Notification,OwnerNotification
from typing import List
from datetime import datetime, timedelta

owner_bp = Blueprint('owner', __name__)


@owner_bp.route('/reservations', methods=['GET'])
@login_required
def view_reservations():
    """Display all reservations for the owner's cottages"""
    if not current_user.is_owner:
        flash('Access denied. Owner privileges required.', 'error')
        return redirect(url_for('main.index'))
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get all reservations for cottages owned by this user
        cursor.execute("""
            SELECT r.id, r.cottage_id, oc.cottage_no, r.table_id, ct.table_no, 
                   r.date_stay, r.start_time, r.end_time, r.max_persons, r.amount,
                   r.cottage_status, r.user_id, u.name as guest_name, r.date_reserved,
                   r.amenities_id
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN cottage_tables ct ON r.table_id = ct.id
            JOIN users u ON r.user_id = u.id
            WHERE oc.user_id = ?
            ORDER BY r.date_stay DESC, r.start_time ASC
        """, (current_user.id,))
        
        reservations = cursor.fetchall()
        
        # Get unread notifications count
        unread_count = OwnerNotification.get_unread_count(conn, current_user.id)
        
        return render_template('owner/reservations.html', 
                              reservations=reservations, 
                              unread_count=unread_count)
    
    except Exception as e:
        flash(f'Error retrieving reservations: {str(e)}', 'error')
        return redirect(url_for('owner.dashboard'))
    finally:
        conn.close()

@owner_bp.route('/reservations/approve/<int:reservation_id>', methods=['POST'])
@login_required
def approve_reservation(reservation_id):
    """Approve a pending reservation"""
    if not current_user.is_owner:
        flash('Access denied. Owner privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify this reservation belongs to one of the owner's cottages
        cursor.execute("""
            SELECT r.id
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ? AND oc.user_id = ? AND r.cottage_status = 'pending'
        """, (reservation_id, current_user.id))
        
        if not cursor.fetchone():
            flash('Invalid reservation or not authorized to approve.', 'error')
            return redirect(url_for('owner.view_reservations'))
        
        # Update reservation status
        cursor.execute("""
            UPDATE reservations
            SET cottage_status = 'reserved'
            WHERE id = ?
        """, (reservation_id,))
        
        # Create notification for the guest
        Notification.create_approval_notification(conn, reservation_id, approved=True)
        
        conn.commit()
        flash('Reservation approved successfully!', 'success')
        return redirect(url_for('owner.view_reservations'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Error approving reservation: {str(e)}', 'error')
        return redirect(url_for('owner.view_reservations'))
    finally:
        conn.close()

@owner_bp.route('/reservations/decline/<int:reservation_id>', methods=['POST'])
@login_required
def decline_reservation(reservation_id):
    """Decline a pending reservation"""
    if not current_user.is_owner:
        flash('Access denied. Owner privileges required.', 'error')
        return redirect(url_for(''))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify this reservation belongs to one of the owner's cottages
        cursor.execute("""
            SELECT r.id
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ? AND oc.user_id = ? AND r.cottage_status = 'pending'
        """, (reservation_id, current_user.id))
        
        if not cursor.fetchone():
            flash('Invalid reservation or not authorized to decline.', 'error')
            return redirect(url_for('owner.view_reservations'))
        
        # Update reservation status
        cursor.execute("""
            UPDATE reservations
            SET cottage_status = 'declined'
            WHERE id = ?
        """, (reservation_id,))
        
       
        Notification.create_cancellation_notification(conn, reservation_id, cancelled_by_user=False)
        
        conn.commit()
        flash('Reservation declined successfully.', 'success')
        return redirect(url_for('owner.view_reservations'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Error declining reservation: {str(e)}', 'error')
        return redirect(url_for('owner.view_reservations'))
    finally:
        conn.close()
 
@owner_bp.route('/owner-notifications')
@login_required
def owner_notifications():
    if current_user == 'owner':
        flash('Access denied. Owner privileges required.', 'error')
        return redirect(url_for('owner.owener_dashboard'))
        
    conn = get_db_connection()
    try:    

        notifications = OwnerNotification.get_all_notifications(conn, current_user.id)
        
        unread_count = OwnerNotification.get_unread_count(conn, current_user.id)
        
        return render_template('notifications.html', 
                              notifications=notifications, 
                              unread_count=unread_count,
                              user=current_user)
    except Exception as e:
        flash(f'Error retrieving notifications: {str(e)}', 'error')
        return redirect(url_for('owner.dashboard'))
    finally:
        conn.close()


@owner_bp.route('/owner-notifications/owner-mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    conn = get_db_connection()
    OwnerNotification.mark_as_read(conn, notification_id, current_user.id)
    conn.close()
    return redirect(url_for('owner.owner_notifications'))

@owner_bp.route('/owner-notifications/owner-delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    conn = get_db_connection()
    OwnerNotification.delete_notification(conn, notification_id, current_user.id)
    conn.close()
    return redirect(url_for('owner.owner_notifications'))

@owner_bp.route('/owner-notifications/owner-delete-all', methods=['POST'])
@login_required
def delete_all_notifications():
    conn = get_db_connection()
    OwnerNotification.delete_all_notifications(conn, current_user.id)
    conn.close()
    return redirect(url_for('owner.owner_notifications'))


@owner_bp.route('/notifications/owner-mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    conn = get_db_connection()
    OwnerNotification.mark_all_as_read(conn, current_user.id)
    conn.close()
    return redirect(url_for('owner.owner_notifications'))