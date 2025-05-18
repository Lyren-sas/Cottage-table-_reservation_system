from flask_login import current_user
from website import create_app_1, get_db_connection
from website.models import Notification, OwnerNotification

if __name__ == '__main__':  
    app = create_app_1()
    
    @app.context_processor
    def inject_notification_data():
        conn = get_db_connection()
        if current_user.is_authenticated and current_user.role == 'user': 
            unread_count = Notification.get_unread_count(conn, current_user.id)
        elif current_user.is_authenticated and current_user.role == 'owner':
            unread_count = OwnerNotification.get_unread_count(conn, current_user.id)
        else:
            unread_count = 0
        conn.close()
        return dict(unread_count=unread_count)
        
    app.run(debug=True, host='0.0.0.0', port=7422)