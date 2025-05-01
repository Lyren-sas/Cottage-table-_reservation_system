from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from .models import get_db_connection
from .models import Notification, OwnerNotification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications')
@login_required
def notifications():
    conn = get_db_connection()
    try:
        notifications = Notification.get_user_notifications(conn, current_user.id)
        # Get unread notifications count
        unread_count = Notification.get_unread_count(conn, current_user.id)
        
        return render_template('notifications.html', 
                              notifications=notifications, 
                              unread_count=unread_count,
                              user=current_user)
    except Exception as e:
        flash(f'Error retrieving notifications: {str(e)}', 'error')
        return redirect(url_for('view.landing'))
    finally:
        conn.close()

@notifications_bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    conn = get_db_connection()
    Notification.mark_as_read(conn, notification_id, current_user.id)
    conn.close()
    return redirect(url_for('notifications.notifications'))

@notifications_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    conn = get_db_connection()
    Notification.mark_all_as_read(conn, current_user.id)
    conn.close()
    return redirect(url_for('notifications.notifications'))


@notifications_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    conn = get_db_connection()
    Notification.delete_notification(conn, notification_id, current_user.id)
    conn.close()
    return redirect(url_for('notifications.notifications'))

@notifications_bp.route('/notifications/delete-all', methods=['POST'])
@login_required
def delete_all_notifications():
    conn = get_db_connection()
    Notification.delete_all_notifications(conn, current_user.id)
    conn.close()
    return redirect(url_for('notifications.notifications'))

