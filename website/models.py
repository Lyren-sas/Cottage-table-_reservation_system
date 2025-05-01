from flask import flash
from flask_login import UserMixin
from datetime import datetime
import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    
    conn = sqlite3.connect('database.db')  # Replace with your actual database name
    conn.row_factory = sqlite3.Row 
    return conn

class User(UserMixin):
    def __init__(self, id=None, email=None, username=None, password=None, date_created=None, name=None, role=None, user_image=None, user_phone=None):
        self.id = id
        self.email = email
        self.username = username
        self.password = password
        
        # Convert date_created from string to datetime if needed
        if date_created and isinstance(date_created, str):
            try:
                self.date_created = datetime.strptime(date_created, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                self.date_created = datetime.utcnow()
        else:
            self.date_created = date_created or datetime.utcnow()
            
        self.name = name
        self.role = role or "user"
        self.user_image = user_image
        self.phone = user_phone
    
    @classmethod
    def get_user_by_email(cls, conn, email):
        conn.row_factory = sqlite3.Row  # Ensure dict-like access
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND role = "user"', (email,))
        user_data = cursor.fetchone()
        if user_data:
            return cls(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['user_pass'],
                date_created=user_data['date_created'],
                name=user_data['name'],
                role=user_data['role'],
                user_image=user_data['user_image'],
                user_phone=user_data['phone']  # Get phone from database 'phone' column
            )
        return None
    @classmethod
    def get_user_by_id(cls, conn, user_id):
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return cls(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['user_pass'],
                date_created=user_data['date_created'],
                name=user_data['name'],
                role=user_data['role'],
                user_image=user_data['user_image'],
                user_phone=user_data['phone']  # Get phone from database 'phone' column
            )
        return None
    
    @classmethod
    def get_user_by_username(cls, conn, username):
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        if user_data:
            return cls(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['user_pass'],
                date_created=user_data['date_created'],
                name=user_data['name'],
                role=user_data['role'],
                user_image=user_data['user_image'],
                user_phone=user_data['phone']  # Get phone from database 'phone' column
            )
        return None
    
    def save_to_db(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO users (email, username, user_pass, date_created, name, role, user_image, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (self.email, self.username, self.password, self.date_created, self.name, self.role, self.user_image, self.phone)
        )
        conn.commit()
        self.id = cursor.lastrowid
        return self.id
    
    # This method is redundant as we already have the phone attribute, but keeping for compatibility
    def get_phone(self, conn):  
        cursor = conn.cursor()
        cursor.execute('SELECT phone FROM users WHERE id = ?', (self.id,))
        user_data = cursor.fetchone()
        if user_data:
            return user_data['phone']
        return None
    
    def update_in_db(self, conn):
        if not self.id:
            raise ValueError("User must have an ID to update.")
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE users 
            SET email = ?, username = ?, user_pass = ?, date_created = ?, name = ?, role = ?, user_image = ?, phone = ?
            WHERE id = ?
            ''',
            (self.email, self.username, self.password, self.date_created, self.name, self.role, self.user_image, self.phone, self.id)
        )
        conn.commit()  # Added commit which was missing in original code

class Owner(UserMixin):     
    def __init__(self, id=None, email=None, username=None, password=None, date_created=None, name=None, role=None, user_image=None, phone=None, notification_pref=None, preferred_location=None):         
        self.id = id         
        self.email = email         
        self.username = username         
        self.password = password         
        self.date_created = date_created or datetime.utcnow()         
        self.name = name         
        self.role = role or "owner"         
        self.user_image = user_image         
        self.phone = phone         
        self.notification_pref = notification_pref         
        self.preferred_location = preferred_location      
    
    @classmethod     
    def get_owner_by_email(cls, conn, email):         
        cursor = conn.cursor()         
        cursor.execute('SELECT * FROM users WHERE email = ? AND role = "owner"', (email,))         
        user_data = cursor.fetchone()         
        if user_data:             
            return cls(                 
                id=user_data['id'],                 
                email=user_data['email'],                 
                username=user_data['username'],                 
                password=user_data['user_pass'],                 
                date_created=user_data['date_created'],                 
                name=user_data['name'],                 
                role=user_data['role'],                 
                user_image=user_data['user_image'],                 
                phone=user_data['phone'] if 'phone' in user_data.keys() else None             
            )         
        return None      
    
    @classmethod     
    def get_owner_by_username(cls, conn, username):         
        cursor = conn.cursor()         
        cursor.execute('SELECT * FROM users WHERE username = ? AND role = "owner"', (username,))         
        user_data = cursor.fetchone()         
        if user_data:             
            return cls(                 
                id=user_data['id'],                 
                email=user_data['email'],                 
                username=user_data['username'],                 
                password=user_data['user_pass'],                 
                date_created=user_data['date_created'],                 
                name=user_data['name'],                 
                role=user_data['role'],                 
                user_image=user_data['user_image'],                 
                phone=user_data['phone'] if 'phone' in user_data.keys() else None         
            )         
        return None              
    
    def update_in_db(self, conn):         
        """         
        Update owner information in the database.         
        This method is called when updating profile information.         
        """         
        cursor = conn.cursor()         
        cursor.execute('''             
            UPDATE users              
            SET name = ?, phone = ?, user_image = ?,                  
                notification_pref = ?, preferred_location = ?, user_pass = ?             
            WHERE id = ?         
        ''', (             
            self.name,              
            self.phone,              
            self.user_image,             
            self.notification_pref,             
            self.preferred_location,             
            self.password,             
            self.id         
        ))         
        conn.commit()         
        return True

    


class OwnerCottage:
    def __init__(self, user_id, owner_name, cottage_no, flag_color=None, cottage_image=None, 
                 cottage_location=None, cottage_description=None, status="available", id=None):
        self.id = id
        self.user_id = user_id
        self.owner_name = owner_name
        self.cottage_no = cottage_no
        self.flag_color = flag_color
        self.cottage_image = cottage_image
        self.cottage_location = cottage_location
        self.cottage_description = cottage_description
        self.status = status

    def save_to_db(self, conn):
        cursor = conn.execute(
            '''INSERT INTO owner_cottages 
            (user_id, owner_name, cottage_no, flag_color, cottage_image, cottage_location, cottage_description) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (self.user_id, self.owner_name, self.cottage_no, self.flag_color, 
             self.cottage_image, self.cottage_location, self.cottage_description)
        )
        self.id = cursor.lastrowid
        return self

    def update_in_db(self, conn):
        conn.execute(
            '''UPDATE owner_cottages 
            SET cottage_no = ?, flag_color = ?, cottage_image = ?, 
            cottage_location = ?, cottage_description = ? 
            WHERE id = ?''',
            (self.cottage_no, self.flag_color, self.cottage_image, 
             self.cottage_location, self.cottage_description, self.id)
        )
        return self

    @staticmethod
    def delete_from_db(conn, cottage_id):
        conn.execute('DELETE FROM owner_cottages WHERE id = ?', (cottage_id,))
        return True

    @staticmethod
    def get_by_id(conn, cottage_id):
        cottage = conn.execute('SELECT * FROM owner_cottages WHERE id = ?', (cottage_id,)).fetchone()
        if cottage:
            return OwnerCottage(
                id=cottage['id'],
                user_id=cottage['user_id'],
                owner_name=cottage['owner_name'],
                cottage_no=cottage['cottage_no'],
                flag_color=cottage['flag_color'],
                cottage_image=cottage['cottage_image'],
                cottage_location=cottage['cottage_location'],
                cottage_description=cottage['cottage_description'],
                status=cottage['cottage_status']
            )
        return None

    @staticmethod
    def get_cottages_by_user_id(conn, user_id):
        try:
            cursor = conn.execute(
                """SELECT id, user_id, owner_name, cottage_no, flag_color, cottage_image, 
                          cottage_location, cottage_description, cottage_status
                   FROM owner_cottages 
                   WHERE user_id = ?""", 
                (user_id,)
            )
            cottages = []
            for row in cursor.fetchall():
                # Convert the SQLite row to a cottage object
                cottage = OwnerCottage(
                    user_id=row['user_id'],
                    owner_name=row['owner_name'],
                    cottage_no=row['cottage_no'],
                    flag_color=row['flag_color'],
                    cottage_image=row['cottage_image'],
                    cottage_location=row['cottage_location'],
                    cottage_description=row['cottage_description'],
                    status=row['cottage_status'],
                    id=row['id']
                )
                cottages.append(cottage)
            return cottages
        except Exception as e:
            flash(f"Error in get_cottages_by_user_id: {str(e)}")
            raise e


class CottageTable:
    def __init__(self, cottage_id, table_no, capacity, table_image=None, price = None, status="available", id=None):
        self.id = id
        self.cottage_id = cottage_id
        self.table_no = table_no
        self.capacity = capacity
        self.table_image = table_image
        self.price = price
        self.status = status
    
    def save_to_db(self, conn):
        cursor = conn.execute(
            'INSERT INTO cottage_tables (cottage_id, table_no, capacity, table_image,price, status) VALUES (?, ?, ?, ?, ?, ?)',
            (self.cottage_id, self.table_no, self.capacity, self.table_image, self.price, self.status)
        )
        self.id = cursor.lastrowid
        return self.id
    
    def update_in_db(self, conn):
        conn.execute(
            'UPDATE cottage_tables SET table_no = ?, capacity = ?, table_image = ?,price=? status = ? WHERE id = ?',
            (self.table_no, self.capacity, self.table_image, self.price, self.status, self.id)
        )
        return self
    
    @staticmethod
    def delete_from_db(conn, table_id):
        conn.execute('DELETE FROM cottage_tables WHERE id = ?', (table_id,))
        return True
    
    @staticmethod
    def delete_by_cottage_id(conn, cottage_id):
        conn.execute('DELETE FROM cottage_tables WHERE cottage_id = ?', (cottage_id,))
        return True
    
    @staticmethod
    def get_by_id(conn, table_id):
        table = conn.execute('SELECT * FROM cottage_tables WHERE id = ?', (table_id,)).fetchone()
        if table:
            return CottageTable(
                id=table['id'],
                cottage_id=table['cottage_id'],
                table_no=table['table_no'],
                capacity=table['capacity'],
                table_image=table['table_image'],
                price=table['price'],
                status=table['status']
            )
        return None
    
    @staticmethod
    def get_by_cottage_id(conn, cottage_id):
        tables = conn.execute('SELECT * FROM cottage_tables WHERE cottage_id = ?', (cottage_id,)).fetchall()
        return [CottageTable(
            id=table['id'],
            cottage_id=table['cottage_id'],
            table_no=table['table_no'],
            capacity=table['capacity'],
            table_image=table['table_image'],
            price=table['price'],
            status=table['status']
        ) for table in tables]




class CottageDiscovery:
    """Model for cottage discoveries."""
    
    def __init__(self, id=None, cottage_id=None, image_filename=None, description=None, created_at=None, image_data=None):
        self.id = id
        self.cottage_id = cottage_id
        self.image_filename = image_filename
        self.description = description
        self.created_at = created_at
        self.image_data = image_data
                    
    @staticmethod
    def create_table(conn):
        """Create the cottage_discoveries table if it doesn't exist."""
        
        query = """
        CREATE TABLE IF NOT EXISTS cottage_discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cottage_id INTEGER NOT NULL,
            image_filename TEXT,
            image_data BLOB,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cottage_id) REFERENCES owner_cottages(id) ON DELETE CASCADE
        )
        """
        conn.execute(query)
        
    def save_to_db(self, conn):
        """Save discovery to database (create or update)."""
        if self.id:
            # Update existing discovery
            query = """
            UPDATE cottage_discoveries
            SET cottage_id = ?, image_filename = ?, description = ?
            WHERE id = ?
            """
            conn.execute(query, (self.cottage_id, self.image_filename, self.description, self.id))
            
            # Update image data if provided
            if self.image_data is not None:
                query = """
                UPDATE cottage_discoveries
                SET image_data = ?
                WHERE id = ?
                """
                conn.execute(query, (self.image_data, self.id))
        else:
            # Create new discovery
            if self.image_data is not None:
                # Save with image data
                query = """
                INSERT INTO cottage_discoveries (cottage_id, image_filename, description, image_data)
                VALUES (?, ?, ?, ?)
                """
                cursor = conn.execute(query, (self.cottage_id, self.image_filename, self.description, self.image_data))
            else:
                # Save without image data
                query = """
                INSERT INTO cottage_discoveries (cottage_id, image_filename, description)
                VALUES (?, ?, ?)
                """
                cursor = conn.execute(query, (self.cottage_id, self.image_filename, self.description))
            
            self.id = cursor.lastrowid
        
        conn.commit()
        return self.id
        
    @classmethod
    def create(cls, conn, cottage_id, image_filename=None, description=None, image_data=None):
        """Add a new discovery to the database."""
        discovery = cls(
            cottage_id=cottage_id,
            image_filename=image_filename,
            description=description,
            image_data=image_data
        )
        discovery.save_to_db(conn)
        return discovery.id
    
    @classmethod
    def get_by_id(cls, conn, discovery_id):
        """Get a discovery by its ID."""
        query = """
        SELECT id, cottage_id, image_filename, description, created_at
        FROM cottage_discoveries
        WHERE id = ?
        """
        cursor = conn.execute(query, (discovery_id,))
        row = cursor.fetchone()
        
        if row:
            return cls(
                id=row[0],
                cottage_id=row[1],
                image_filename=row[2],
                description=row[3],
                created_at=row[4]
            )
        return None
    
    @classmethod
    def get_all_for_cottage(cls, conn, cottage_id):
        """Get all discoveries for a specific cottage."""
        query = """
        SELECT id, cottage_id, image_filename, description, created_at
        FROM cottage_discoveries
        WHERE cottage_id = ?
        ORDER BY created_at DESC
        """
        cursor = conn.execute(query, (cottage_id,))
        rows = cursor.fetchall()
        
        discoveries = []
        for row in rows:
            discoveries.append(cls(
                id=row[0],
                cottage_id=row[1],
                image_filename=row[2],
                description=row[3],
                created_at=row[4]
            ))
        
        return discoveries
    
    @classmethod
    def update(cls, conn, discovery_id, image_filename=None, description=None, image_data=None):
        """Update an existing discovery."""
        # Build the update query dynamically based on what's being updated
        query_parts = []
        params = []
        
        if image_filename is not None:
            query_parts.append("image_filename = ?")
            params.append(image_filename)
        
        if description is not None:
            query_parts.append("description = ?")
            params.append(description)
        
        if query_parts:
            query = f"""
            UPDATE cottage_discoveries
            SET {', '.join(query_parts)}
            WHERE id = ?
            """
            params.append(discovery_id)
            
            conn.execute(query, params)
        
        # Handle image data separately if provided
        if image_data is not None:
            query = """
            UPDATE cottage_discoveries
            SET image_data = ?
            WHERE id = ?
            """
            conn.execute(query, (image_data, discovery_id))
        
        conn.commit()
        return True
    
    @classmethod
    def delete(cls, conn, discovery_id):
        """Delete a discovery."""
        query = """
        DELETE FROM cottage_discoveries
        WHERE id = ?
        """
        conn.execute(query, (discovery_id,))
        conn.commit()
        return True
    
    @classmethod
    def get_image_data(cls, conn, discovery_id):
        """Get image data for a discovery."""
        query = """
        SELECT image_data
        FROM cottage_discoveries
        WHERE id = ?
        """
        cursor = conn.execute(query, (discovery_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            return row[0]
        return None
    


    
class Reservation:
    def __init__(self, id=None, user_id=None, cottage_id=None, table_id=None, amenities_id=None, max_persons=None,
                 date_stay=None, start_time=None, end_time=None, amount=None, cottage_status=None,
                 date_reserved=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.cottage_id = cottage_id
        self.table_id = table_id
        self.amenities_id = amenities_id
        self.max_persons = max_persons
        self.date_stay = date_stay
        self.start_time = start_time
        self.end_time = end_time
        self.amount = amount
        self.cottage_status = cottage_status
        self.date_reserved = date_reserved

        # Accept and assign extra dynamic fields (guest_name, cottage_image, etc.)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def update_status(self, conn, new_status):
        cursor = conn.cursor()
        cursor.execute('UPDATE reservations SET cottage_status = ? WHERE id = ?', (new_status, self.id))
        conn.commit()
        self.cottage_status = new_status
        return True

    @classmethod
    def get_reservations_by_user_id(cls, conn, user_id):
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reservations WHERE user_id = ?', (user_id,))
        reservation_rows = cursor.fetchall()
        return [cls(
            id=row['id'],
            user_id=row['user_id'],
            cottage_id=row['cottage_id'],
            table_id=row['table_id'] if 'table_id' in row else None,
            amenities_id=row['amenities_id'] if 'amenities_id' in row else None,
            max_persons=row['max_persons'] if 'max_persons' in row else None,
            date_stay=row['date_stay'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            amount=row['amount'],
            cottage_status=row['cottage_status'],
            date_reserved=row['date_reserved']
        ) for row in reservation_rows]
    
    @classmethod
    def find_conflicting_reservations(cls, conn, cottage_id, date_stay, start_time, end_time):
        cursor = conn.cursor()
       
        cursor.execute('''
            SELECT * FROM reservations 
            WHERE cottage_id = ? 
            AND date_stay = ? 
            AND cottage_status IN ("reserved", "approved") 
            AND (
                (? BETWEEN start_time AND end_time) OR 
                (? BETWEEN start_time AND end_time) OR 
                (start_time BETWEEN ? AND ?) OR 
                (end_time BETWEEN ? AND ?)
            )
        ''', (cottage_id, date_stay, start_time, end_time, start_time, end_time, start_time, end_time))
        return cursor.fetchall()
    
    def save_to_db(self, conn):
        cursor = conn.cursor()
       
        cursor.execute(
            '''
            INSERT INTO reservations 
            (user_id, cottage_id, table_id, amenities_id, max_persons, date_stay, start_time, end_time, amount, cottage_status, date_reserved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (self.user_id, self.cottage_id, self.table_id, self.amenities_id, self.max_persons, self.date_stay, 
             self.start_time, self.end_time, self.amount, self.cottage_status, self.date_reserved)
        )
        conn.commit()
        self.id = cursor.lastrowid
        return self.id
    
    # Added methods that might be missing
    @staticmethod
    def get_reservation_by_id(conn, reservation_id):
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reservations WHERE id = ?', (reservation_id,))
        reservation_data = cursor.fetchone()
        
        if reservation_data:
            return Reservation(
                id=reservation_data['id'],
                user_id=reservation_data['user_id'],
                cottage_id=reservation_data['cottage_id'],
                table_id=reservation_data.get('table_id'),
                amenities_id=reservation_data.get('amenities_id'),
                max_persons=reservation_data.get('max_persons'),
                date_stay=reservation_data['date_stay'],
                start_time=reservation_data['start_time'],
                end_time=reservation_data['end_time'],
                amount=reservation_data['amount'],
                cottage_status=reservation_data['cottage_status'],
                date_reserved=reservation_data['date_reserved']
            )
        return None
    
    def update_status(self, conn, new_status):
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE reservations SET cottage_status = ? WHERE id = ?',
            (new_status, self.id)
        )
        conn.commit()
        self.cottage_status = new_status
        return True


class Amenity:
    def __init__(self, id=None, category=None, ame_price=None, available=None):
        self.id = id
        self.category = category
        self.ame_price = ame_price
        self.available = available

    @classmethod
    def get_all_amenities(cls, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM amenities_1')
        amenity_rows = cursor.fetchall()
        return [cls(
            id=row['id'],
            category=row['category'],
            ame_price=row['ame_price'],
            available=row['available']
        ) for row in amenity_rows]
    
class CottageAmenity:
    """Model for the many-to-many relationship between cottages and amenities"""
    
    def __init__(self, cottage_id, amenity_id,reservation_id=None):
        self.cottage_id = cottage_id
        self.amenity_id = amenity_id
        self.reservation_id = reservation_id
    
    @staticmethod
    def add_amenity_to_cottage(conn, cottage_id, amenity_id,reservation_id):
        """Associate an amenity with a cottage"""
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO cottage_amenities (cottage_id, amenity_id, reservation_id) VALUES (?, ?, ?)',
            (cottage_id, amenity_id,reservation_id)
        )
        return cursor.lastrowid
    
    @staticmethod
    def get_amenities_by_cottage_id(conn, cottage_id):
        """Get all amenities for a specific cottage"""
        cursor = conn.cursor()
        amenities = cursor.execute('''
            SELECT a.* 
            FROM amenities_1 a
            JOIN cottage_amenities ca ON a.id = ca.amenity_id
            WHERE ca.cottage_id = ?
            ORDER BY a.category
        ''', (cottage_id,)).fetchall()
        return amenities
    
    @staticmethod
    def get_amenities_for_cottage(conn, cottage_id):
        """Get all amenities for a specific cottage - alias method called from routes"""
        cursor = conn.cursor()
        amenities = cursor.execute('''
            SELECT a.* 
            FROM amenities_1 a
            JOIN cottage_amenities ca ON a.id = ca.amenity_id
            WHERE ca.cottage_id = ?
        ''', (cottage_id,)).fetchall()
        return amenities

    @staticmethod
    def get_amenity_ids_for_cottage(conn, cottage_id):
        """Get all amenity IDs for a specific cottage - used for pre-selecting checkboxes on edit page"""
        cursor = conn.cursor()
        amenity_ids = cursor.execute('''
            SELECT amenity_id 
            FROM cottage_amenities
            WHERE cottage_id = ?
        ''', (cottage_id,)).fetchall()
        return [row['amenity_id'] for row in amenity_ids]

    @staticmethod
    def remove_all_cottage_amenities(conn, cottage_id):
        """Remove all amenities associated with a cottage - used when updating cottage amenities"""
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cottage_amenities WHERE cottage_id = ?', (cottage_id,))
        return True
    




class Notification:     
    def __init__(self, id, user_id, message, notification_type, status, created_at, reservation_id=None):         
        self.id = id         
        self.user_id = user_id         
        self.message = message         
        self.notification_type = notification_type         
        self.status = status  # 'read' or 'unread'         
        self.created_at = created_at         
        self.reservation_id = reservation_id
               
        self.read = (status == 'read')      
        
    def mark_read(self):         
        """Mark this notification as read"""         
        self.status = 'read'         
        self.read = True
    
    def to_dict(self):
        """Convert notification object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'notification_type': self.notification_type,
            'status': self.status,
            'created_at': self.created_at,
            'read': self.read,
            'reservation_id': self.reservation_id
        }
              
    @staticmethod     
    def get_user_notifications(conn, user_id):         
        cursor = conn.cursor()         
        cursor.execute(             
            """SELECT id, user_id, message, notification_type, status, created_at, reservation_id                 
                FROM notifications                 
                WHERE user_id = ?                 
                ORDER BY created_at DESC""",              
            (user_id,)         
        )         
        notifications = []         
        for row in cursor.fetchall():             
            notifications.append(Notification(                 
                id=row[0],                 
                user_id=row[1],                 
                message=row[2],                 
                notification_type=row[3],                 
                status=row[4],                 
                created_at=row[5],
                reservation_id=row[6] if len(row) > 6 else None
            ))         
        return notifications     
    
    @staticmethod
    def create_decline_notification(conn, reservation_id, decline_reason=None):
        """Create notification for a declined reservation"""
        cursor = conn.cursor()
    
        # Get reservation details
        cursor.execute("""
            SELECT r.user_id, oc.cottage_no, r.date_stay, r.start_time, r.end_time
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        user_id, cottage_no, date_stay, start_time, end_time = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        notification_message = (
            f"Your reservation for Cottage #{cottage_no} on {date_formatted} from {time_range} "
            f"has been declined."
        )
        
        # Add reason if provided
        if decline_reason:
            notification_message += f" Reason: {decline_reason}"
        
        # Insert notification
        cursor.execute("""
            INSERT INTO notifications (user_id, message, notification_type, status, created_at, reservation_id)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        """, (user_id, notification_message, 'decline', 'unread', reservation_id))
        
        conn.commit()
        return True

    @staticmethod     
    def get_unread_count(conn, user_id):         
        cursor = conn.cursor()         
        cursor.execute(             
            """SELECT COUNT(*)                 
                FROM notifications                 
                WHERE user_id = ? AND status = 'unread'""",              
            (user_id,)         
        )         
        unread_count = cursor.fetchone()[0]         
        return unread_count     
    
    @staticmethod     
    def mark_as_read(conn, notification_id, user_id):         
        cursor = conn.cursor()         
        cursor.execute(             
            """UPDATE notifications                 
                SET status = 'read'                 
                WHERE id = ? AND user_id = ?""",              
            (notification_id, user_id)         
        )         
        conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod     
    def mark_all_as_read(conn, user_id):         
        cursor = conn.cursor()         
        cursor.execute(             
            """UPDATE notifications                 
                SET status = 'read'                 
                WHERE user_id = ?""",              
            (user_id,)         
        )         
        conn.commit()
        return cursor.rowcount
    
    @staticmethod     
    def delete_notification(conn, notification_id, user_id):         
        cursor = conn.cursor()         
        cursor.execute(             
            """DELETE FROM notifications                 
                WHERE id = ? AND user_id = ?""",              
            (notification_id, user_id)         
        )         
        conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod     
    def delete_all_notifications(conn, user_id):         
        cursor = conn.cursor()         
        cursor.execute(             
            """DELETE FROM notifications                 
                WHERE user_id = ?""",              
            (user_id,)         
        )         
        conn.commit()
        return cursor.rowcount

    @staticmethod
    def create_reservation_notification(conn, reservation_id):
        """Create notification for a new reservation"""
        cursor = conn.cursor()
        
        # Get reservation details
        cursor.execute("""
            SELECT r.user_id, oc.cottage_no, ct.table_no, r.date_stay, r.start_time, r.end_time, 
                   r.max_persons, r.amount
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN cottage_tables ct ON r.table_id = ct.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        user_id, cottage_no, table_no, date_stay, start_time, end_time, max_persons, amount = reservation
        
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
       
        notification_message = (
            f"Your reservation for Cottage #{cottage_no} with Table #{table_no} on {date_formatted} from {time_range} "
            f"for {max_persons} person(s) with a total amount of ₱{amount} is now pending. Please wait for the owner's approval."
        )
        
        # Insert notification
        cursor.execute("""
            INSERT INTO notifications (user_id, message, notification_type, status, created_at, reservation_id)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        """, (user_id, notification_message, 'reservation', 'unread', reservation_id))
        
        conn.commit()
        return True
        
    @staticmethod
    def create_cancellation_notification(conn, reservation_id, cancelled_by_user=True):
        """Create notification for a cancelled reservation"""
        cursor = conn.cursor()
        
        # Get reservation details
        cursor.execute("""
            SELECT r.user_id, r.cottage_id, oc.user_id as owner_id, oc.cottage_no, 
                   r.date_stay, r.start_time, r.end_time
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        user_id, cottage_id, owner_id, cottage_no, date_stay, start_time, end_time = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        # Create notification based on who cancelled
        if cancelled_by_user:
            # Notify owner that user cancelled
            notification_message = (
                f"A reservation for Cottage #{cottage_no} on {date_formatted} from {time_range} "
                f"has been cancelled by the guest."
            )
            notif_user_id = owner_id
        else:
            # Notify user that owner declined
            notification_message = (
                f"Your reservation for Cottage #{cottage_no} on {date_formatted} from {time_range} "
                f"has been declined by the owner."
            )
            notif_user_id = user_id
        
        # Insert notification
        cursor.execute("""
            INSERT INTO notifications (user_id, message, notification_type, status, created_at, reservation_id)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        """, (notif_user_id, notification_message, 'cancellation', 'unread', reservation_id))
        
        conn.commit()
        return True
        
    @staticmethod
    def create_approval_notification(conn, reservation_id, approved=True):
        """Create notification for an approved reservation"""
        cursor = conn.cursor()
        
        # Get reservation details
        cursor.execute("""
            SELECT r.user_id, oc.cottage_no, r.date_stay, r.start_time, r.end_time
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        user_id, cottage_no, date_stay, start_time, end_time = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        notification_message = (
            f"Your reservation for Cottage #{cottage_no} on {date_formatted} from {time_range} "
            f"has been approved! Please arrive on time."
        )
        
        # Insert notification
        cursor.execute("""
            INSERT INTO notifications (user_id, message, notification_type, status, created_at, reservation_id)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        """, (user_id, notification_message, 'approval', 'unread', reservation_id))
        
        conn.commit()
        return True
        
    @staticmethod     
    def filter_notifications(conn, user_id, notification_type='all', status='all'):
        """Filter notifications by type and status"""
        cursor = conn.cursor()
        
        query = """
            SELECT id, user_id, message, notification_type, status, created_at, reservation_id
            FROM notifications
            WHERE user_id = ?
        """
        params = [user_id]
        
        # Add type filter if specified
        if notification_type != 'all':
            query += " AND notification_type = ?"
            params.append(notification_type)
        
        # Add status filter if specified
        if status != 'all':
            query += " AND status = ?"
            params.append(status)
        
        # Add ordering
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append(Notification(
                id=row[0],
                user_id=row[1],
                message=row[2],
                notification_type=row[3],
                status=row[4],
                created_at=row[5],
                reservation_id=row[6] if len(row) > 6 else None
            ))
        
        return notifications

class OwnerNotification:
    """Model for notifications related to cottage owners"""
    
    def __init__(self, id, owner_id, message, notification_type, status, created_at, 
                 reservation_id=None, guest_id=None, cottage_id=None, 
                 is_actionable=True, action_taken=None, action_at=None):
        """Initialize an owner notification object"""
        self.id = id
        self.owner_id = owner_id
        self.message = message
        self.notification_type = notification_type
        self.status = status  # 'read' or 'unread'
        self.created_at = created_at
        self.reservation_id = reservation_id
        self.guest_id = guest_id
        self.cottage_id = cottage_id
        self.is_actionable = is_actionable
        self.action_taken = action_taken  # 'approved', 'declined', or None
        self.action_at = action_at
        
        # Convenience property
        self.read = (status == 'read')
    
    def mark_read(self, conn):
        """Mark this notification as read"""
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE owner_notifications 
               SET status = 'read' 
               WHERE id = ?""",
            (self.id,)
        )
        conn.commit()
        self.status = 'read'
        self.read = True
        return True
    
    def record_action(self, conn, action):
        """Record action taken on notification (approve/decline)"""
        if action not in ['approved', 'declined']:
            return False
            
        from datetime import datetime
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            """UPDATE owner_notifications 
               SET action_taken = ?, action_at = ?, is_actionable = 0 
               WHERE id = ?""",
            (action, now, self.id)
        )
        conn.commit()
        
        self.action_taken = action
        self.action_at = now
        self.is_actionable = False
        return True
    
    def to_dict(self):
        """Convert notification object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'message': self.message,
            'notification_type': self.notification_type,
            'status': self.status,
            'created_at': self.created_at,
            'reservation_id': self.reservation_id,
            'guest_id': self.guest_id,
            'cottage_id': self.cottage_id,
            'is_actionable': self.is_actionable,
            'action_taken': self.action_taken,
            'action_at': self.action_at,
            'read': self.read
        }
    
    @staticmethod
    def create_reservation_notification(conn, reservation_id):
        """Create notification for cottage owner about a new reservation"""
        cursor = conn.cursor()
        
        # Get reservation and owner details
        cursor.execute("""
            SELECT r.id, oc.id as cottage_id, oc.user_id as owner_id, 
                   r.user_id as guest_id, u.name as guest_name,
                   oc.cottage_no, ct.table_no, r.date_stay, r.start_time, r.end_time, 
                   r.max_persons, r.amount
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN cottage_tables ct ON r.table_id = ct.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        resv_id, cottage_id, owner_id, guest_id, guest_name, cottage_no, table_no, date_stay, \
            start_time, end_time, max_persons, amount = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        # Create owner notification message
        notification_message = (
            f"New reservation request from {guest_name} for your Cottage #{cottage_no} with Table #{table_no} on "
            f"{date_formatted} from {time_range}. Party size: {max_persons} person(s). "
            f"Amount: ₱{amount}. Please approve or decline this request."
        )
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, reservation_id, message, notification_type, status, 
                guest_id, cottage_id, is_actionable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            owner_id, resv_id, notification_message, 'new_reservation', 'unread', 
            guest_id, cottage_id, True
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_cancellation_notification(conn, reservation_id):
        """Create notification for owner when a user cancels their reservation"""
        cursor = conn.cursor()
        
        # Get reservation and owner details
        cursor.execute("""
            SELECT r.id, oc.id as cottage_id, oc.user_id as owner_id, r.user_id as guest_id, 
                   u.name as guest_name, oc.cottage_no, r.date_stay, r.start_time, r.end_time
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        resv_id, cottage_id, owner_id, guest_id, guest_name, cottage_no, date_stay, start_time, end_time = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        # Create owner notification message for cancellation
        notification_message = (
            f"{guest_name} has cancelled their reservation for your Cottage #{cottage_no} on "
            f"{date_formatted} from {time_range}."
        )
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, reservation_id, message, notification_type, status, 
                guest_id, cottage_id, is_actionable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            owner_id, resv_id, notification_message, 'reservation_cancelled', 'unread', 
            guest_id, cottage_id, False
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_payment_notification(conn, reservation_id, payment_amount):
        """Create notification for owner when payment is received for a reservation"""
        cursor = conn.cursor()
        
        # Get reservation and owner details
        cursor.execute("""
            SELECT r.id, oc.id as cottage_id, oc.user_id as owner_id, r.user_id as guest_id, 
                   u.name as guest_name, oc.cottage_no, r.date_stay
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        resv_id, cottage_id, owner_id, guest_id, guest_name, cottage_no, date_stay = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        
        # Create owner notification message for payment
        notification_message = (
            f"Payment of ₱{payment_amount} received from {guest_name} for their reservation of "
            f"Cottage #{cottage_no} on {date_formatted}."
        )
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, reservation_id, message, notification_type, status, 
                guest_id, cottage_id, is_actionable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            owner_id, resv_id, notification_message, 'payment_received', 'unread', 
            guest_id, cottage_id, False
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_system_notification(conn, owner_id, message, notification_type='system'):
        """Create a system notification for an owner"""
        cursor = conn.cursor()
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, message, notification_type, status, is_actionable
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            owner_id, message, notification_type, 'unread', False
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_all_notifications(conn, owner_id, limit=50):
        """Get all notifications for a cottage owner, optionally limited"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, owner_id, message, notification_type, status, created_at,
                   reservation_id, guest_id, cottage_id, is_actionable, action_taken, action_at
            FROM owner_notifications
            WHERE owner_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (owner_id, limit))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append(OwnerNotification(
                id=row[0],
                owner_id=row[1],
                message=row[2],
                notification_type=row[3],
                status=row[4],
                created_at=row[5],
                reservation_id=row[6],
                guest_id=row[7],
                cottage_id=row[8],
                is_actionable=bool(row[9]),
                action_taken=row[10],
                action_at=row[11]
            ))
        return notifications
    @staticmethod
    def create_reservation_notification(conn, reservation_id):
        """Create notification for cottage owner about a new reservation"""
        cursor = conn.cursor()
        
        # Get reservation and owner details
        cursor.execute("""
            SELECT r.id, oc.id as cottage_id, oc.user_id as owner_id, 
                   r.user_id as guest_id, u.name as guest_name,
                   oc.cottage_no, ct.table_no, r.date_stay, r.start_time, r.end_time, 
                   r.max_persons, r.amount
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN cottage_tables ct ON r.table_id = ct.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        resv_id, cottage_id, owner_id, guest_id, guest_name, cottage_no, table_no, date_stay, \
            start_time, end_time, max_persons, amount = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        # Create owner notification message
        notification_message = (
            f"New reservation request from {guest_name} for your Cottage #{cottage_no} with Table #{table_no} on "
            f"{date_formatted} from {time_range}. Party size: {max_persons} person(s). "
            f"Amount: ₱{amount}. Please approve or decline this request."
        )
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, reservation_id, message, notification_type, status, 
                guest_id, cottage_id, is_actionable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            owner_id, resv_id, notification_message, 'new_reservation', 'unread', 
            guest_id, cottage_id, True
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_unread_notifications(conn, owner_id):
        """Get all unread notifications for a cottage owner"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, owner_id, message, notification_type, status, created_at,
                   reservation_id, guest_id, cottage_id, is_actionable, action_taken, action_at
            FROM owner_notifications
            WHERE owner_id = ? AND status = 'unread'
            ORDER BY created_at DESC
        """, (owner_id,))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append(OwnerNotification(
                id=row[0],
                owner_id=row[1],
                message=row[2],
                notification_type=row[3],
                status=row[4],
                created_at=row[5],
                reservation_id=row[6],
                guest_id=row[7],
                cottage_id=row[8],
                is_actionable=bool(row[9]),
                action_taken=row[10],
                action_at=row[11]
            ))
        return notifications
    
    @staticmethod
    def get_actionable_notifications(conn, owner_id):
        """Get all notifications requiring action for a cottage owner"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, owner_id, message, notification_type, status, created_at,
                   reservation_id, guest_id, cottage_id, is_actionable, action_taken, action_at
            FROM owner_notifications
            WHERE owner_id = ? AND is_actionable = 1
            ORDER BY created_at DESC
        """, (owner_id,))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append(OwnerNotification(
                id=row[0],
                owner_id=row[1],
                message=row[2],
                notification_type=row[3],
                status=row[4],
                created_at=row[5],
                reservation_id=row[6],
                guest_id=row[7],
                cottage_id=row[8],
                is_actionable=bool(row[9]),
                action_taken=row[10],
                action_at=row[11]
            ))
        return notifications
    
    @staticmethod
    def get_notifications_by_type(conn, owner_id, notification_type):
        """Get all notifications of a specific type for a cottage owner"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, owner_id, message, notification_type, status, created_at,
                   reservation_id, guest_id, cottage_id, is_actionable, action_taken, action_at
            FROM owner_notifications
            WHERE owner_id = ? AND notification_type = ?
            ORDER BY created_at DESC
        """, (owner_id, notification_type))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append(OwnerNotification(
                id=row[0],
                owner_id=row[1],
                message=row[2],
                notification_type=row[3],
                status=row[4],
                created_at=row[5],
                reservation_id=row[6],
                guest_id=row[7],
                cottage_id=row[8],
                is_actionable=bool(row[9]),
                action_taken=row[10],
                action_at=row[11]
            ))
        return notifications
    
    @staticmethod
    def get_notification_by_id(conn, notification_id, owner_id):
        """Get a specific notification by ID for a cottage owner"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, owner_id, message, notification_type, status, created_at,
                   reservation_id, guest_id, cottage_id, is_actionable, action_taken, action_at
            FROM owner_notifications
            WHERE id = ? AND owner_id = ?
        """, (notification_id, owner_id))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return OwnerNotification(
            id=row[0],
            owner_id=row[1],
            message=row[2],
            notification_type=row[3],
            status=row[4],
            created_at=row[5],
            reservation_id=row[6],
            guest_id=row[7],
            cottage_id=row[8],
            is_actionable=bool(row[9]),
            action_taken=row[10],
            action_at=row[11]
        )
    
    @staticmethod
    def get_unread_count(conn, owner_id):
        """Get count of unread notifications for a cottage owner"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM owner_notifications
            WHERE owner_id = ? AND status = 'unread'
        """, (owner_id,))
        
        return cursor.fetchone()[0]
    
    @staticmethod
    def get_actionable_count(conn, owner_id):
        """Get count of notifications requiring action for a cottage owner"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM owner_notifications
            WHERE owner_id = ? AND is_actionable = 1
        """, (owner_id,))
        
        return cursor.fetchone()[0]
    
    @staticmethod
    def mark_as_read(conn, notification_id, owner_id):
        """Mark a specific notification as read"""
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE owner_notifications
            SET status = 'read'
            WHERE id = ? AND owner_id = ?
        """, (notification_id, owner_id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def mark_all_as_read(conn, owner_id):
        """Mark all notifications for an owner as read"""
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE owner_notifications
            SET status = 'read'
            WHERE owner_id = ? AND status = 'unread'
        """, (owner_id,))
        
        conn.commit()
        return cursor.rowcount
    
    @staticmethod
    def delete_notification(conn, notification_id, owner_id):
        """Delete a specific notification"""
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM owner_notifications
            WHERE id = ? AND owner_id = ?
        """, (notification_id, owner_id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete_all_notifications(conn, owner_id):
        """Delete all notifications for an owner"""
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM owner_notifications
            WHERE owner_id = ?
        """, (owner_id,))
        
        conn.commit()
        return cursor.rowcount
    
    @staticmethod
    def delete_read_notifications(conn, owner_id):
        """Delete all read notifications for an owner"""
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM owner_notifications
            WHERE owner_id = ? AND status = 'read'
        """, (owner_id,))
        
        conn.commit()
        return cursor.rowcount
    
    
    @staticmethod
    def create_decline_notification(conn, reservation_id, decline_reason=None):
        """Create notification for owner when they decline a reservation request"""
        cursor = conn.cursor()
        
        # Get reservation and guest details
        cursor.execute("""
            SELECT r.id, oc.id as cottage_id, oc.user_id as owner_id, r.user_id as guest_id, 
                u.name as guest_name, oc.cottage_no, r.date_stay, r.start_time, r.end_time
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        resv_id, cottage_id, owner_id, guest_id, guest_name, cottage_no, date_stay, start_time, end_time = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        # Create owner notification message confirming they declined the reservation
        notification_message = (
            f"You have declined {guest_name}'s reservation request for Cottage #{cottage_no} on "
            f"{date_formatted} from {time_range}."
        )
        
       
        if decline_reason:
            notification_message += f" Reason: {decline_reason}"
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, reservation_id, message, notification_type, status, 
                guest_id, cottage_id, is_actionable, action_taken, action_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            owner_id, resv_id, notification_message, 'reservation_declined', 'unread', 
            guest_id, cottage_id, False, 'declined'
        ))
        
        conn.commit()
        
        # Also create a notification for the guest using the Notification class
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        guest_message = (
            f"Your reservation for Cottage #{cottage_no} on {date_formatted} from {time_range} "
            f"has been declined by the owner."
        )
        
        if decline_reason:
            guest_message += f" Reason: {decline_reason}"
        
        cursor.execute("""
            INSERT INTO notifications (user_id, message, notification_type, status, created_at, reservation_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guest_id, guest_message, 'decline', 'unread', now, resv_id))
        
        conn.commit()
        return cursor.lastrowid

        
    @staticmethod
    def create_approval_notification(conn, reservation_id):
        """Create notification for owner when they approve a reservation request"""
        cursor = conn.cursor()
        
        # Get reservation and guest details
        cursor.execute("""
            SELECT r.id, oc.id as cottage_id, oc.user_id as owner_id, r.user_id as guest_id, 
                u.name as guest_name, oc.cottage_no, r.date_stay, r.start_time, r.end_time
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        if not reservation:
            return False
            
        resv_id, cottage_id, owner_id, guest_id, guest_name, cottage_no, date_stay, start_time, end_time = reservation
        
        from datetime import datetime
        date_formatted = datetime.strptime(date_stay, '%Y-%m-%d').strftime('%B %d, %Y')
        time_range = f"{start_time} to {end_time}"
        
        # Create owner notification message confirming they approved the reservation
        notification_message = (
            f"You have approved {guest_name}'s reservation request for Cottage #{cottage_no} on "
            f"{date_formatted} from {time_range}."
        )
        
        # Insert notification for owner
        cursor.execute("""
            INSERT INTO owner_notifications (
                owner_id, reservation_id, message, notification_type, status, 
                guest_id, cottage_id, is_actionable, action_taken, action_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            owner_id, resv_id, notification_message, 'reservation_approved', 'unread', 
            guest_id, cottage_id, False, 'approved'
        ))
        
        conn.commit()
        
        # Also create a notification for the guest
        guest_message = (
            f"Good news! Your reservation for Cottage #{cottage_no} on {date_formatted} from {time_range} "
            f"has been approved by the owner. Please proceed with payment to confirm your booking."
        )
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO notifications (user_id, message, notification_type, status, created_at, reservation_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guest_id, guest_message, 'approval', 'unread', now, resv_id))
        
        conn.commit()
        return cursor.lastrowid
        
class Payment:
    """Model for payment records"""

    def __init__(self, id, reservation_id, user_id, amount, payment_method, payment_status, transaction_id):
        self.id = id
        self.reservation_id = reservation_id
        self.user_id = user_id
        self.amount = amount
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.transaction_id = transaction_id
        self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  

    @classmethod
    def create_payment_record(cls, conn, reservation_id, user_id, amount, payment_method, payment_status, transaction_id):
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments (
                reservation_id, user_id, amount,
                payment_method, payment_status, transaction_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (reservation_id, user_id, amount, payment_method, payment_status, transaction_id))
        conn.commit()
        return cursor.lastrowid

    
    