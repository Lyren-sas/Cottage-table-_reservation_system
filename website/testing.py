"""
Testing script to verify database connection and query results.
Add this to a Flask route for testing or run as a standalone script.
"""
import sqlite3
import base64
from flask import jsonify

def test_db_connection(db_path, cottage_id):
    """Test database connection and query for reviews."""
    print(f"Testing database connection to {db_path}")
    print(f"Looking for reviews for cottage ID: {cottage_id}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print("Database connection successful")
        
        # Check if ratings table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ratings'")
        ratings_table = cursor.fetchone()
        
        if not ratings_table:
            print("ERROR: 'ratings' table does not exist!")
            return {"success": False, "message": "Ratings table does not exist"}
        
        print("'ratings' table exists")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ratings)")
        columns = cursor.fetchall()
        print("Ratings table columns:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
        
        # Check if the cottage exists
        cursor.execute("SELECT COUNT(*) FROM cottages WHERE id = ?", (cottage_id,))
        cottage_count = cursor.fetchone()[0]
        
        if cottage_count == 0:
            print(f"ERROR: Cottage ID {cottage_id} does not exist!")
            return {"success": False, "message": f"Cottage ID {cottage_id} does not exist"}
        
        print(f"Cottage ID {cottage_id} exists")
        
        # Run the actual query
        cursor.execute('''
            SELECT
              r.rating_value,
              r.comments,
              r.created_at,
              u.name       AS reviewer_name,
              u.user_image AS reviewer_image
            FROM ratings r
            JOIN users u ON r.user_id = u.id
            WHERE r.cottage_id = ?
            ORDER BY r.created_at DESC
        ''', (cottage_id,))
        
        rows = cursor.fetchall()
        print(f"Query returned {len(rows)} reviews")
        
        # If no reviews, check if there are any reviews at all
        if len(rows) == 0:
            cursor.execute("SELECT COUNT(*) FROM ratings")
            total_reviews = cursor.fetchone()[0]
            print(f"Total reviews in database: {total_reviews}")
            
            if total_reviews > 0:
                # Get some sample cottages that have reviews
                cursor.execute("""
                    SELECT c.id, c.cottage_no, COUNT(r.id) as review_count
                    FROM cottages c
                    JOIN ratings r ON c.id = r.cottage_id
                    GROUP BY c.id
                    ORDER BY review_count DESC
                    LIMIT 3
                """)
                sample_cottages = cursor.fetchall()
                
                if sample_cottages:
                    print("Sample cottages with reviews:")
                    for cottage in sample_cottages:
                        print(f"  - Cottage #{cottage['cottage_no']} (ID: {cottage['id']}) has {cottage['review_count']} reviews")
        
        # Process and return reviews
        reviews = []
        for row in rows:
            img_data = None
            if row['reviewer_image']:
                img_data = base64.b64encode(row['reviewer_image']).decode('ascii')

            review = {
                'rating_value': row['rating_value'],
                'comments': row['comments'],
                'created_at': row['created_at'],
                'name': row['reviewer_name'],
                'image_b64': img_data
            }
            reviews.append(review)
            print(f"Review from {review['name']}: Rating {review['rating_value']}")
        
        conn.close()
        return {"success": True, "reviews": reviews}
    
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return {"success": False, "message": str(e)}

# Example usage
if __name__ == "__main__":
    # Replace with actual database path and cottage ID
    result = test_db_connection("\Desktop\OOP\cottage_reservation\database.db", 1)
    print(result["success"])