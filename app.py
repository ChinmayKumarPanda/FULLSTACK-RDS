from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import logging # For logging

app = Flask(__name__)
db_config = {
    'host': ('your-rds-endpoint.amazonaws.com'), # REPLACE THIS
    'user': ( 'your-username'),                   # REPLACE THIS
    'password': ('your-password'),           # REPLACE THIS
    'database':('your-database-name')           # REPLACE THIS
}

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Connection Function ---
def get_db_connection():
    """Establishes and returns a database connection."""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            logger.info("Successfully connected to the database.")
        return conn
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        return None

# --- Routes ---

# ALB Health Check Route
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for load balancers."""
    logger.info("Health check requested.")
    return jsonify({'status': 'ok', 'message': 'Flask app is running'}), 200

# Get All Students
@app.route('/students', methods=['GET'])
def get_students():
    """Retrieves all students from the database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name, age FROM students ORDER BY id DESC') # Explicitly select columns, order for display
        rows = cursor.fetchall()
        logger.info(f"Retrieved {len(rows)} students.")
        return jsonify(rows)
    except Error as e:
        logger.error(f"Error fetching students: {e}")
        return jsonify({'message': 'Error fetching students', 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed.")


# Get One Student by ID
@app.route('/students/<int:id>', methods=['GET'])
def get_student(id):
    """Retrieves a single student by ID."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name, age FROM students WHERE id = %s', (id,))
        row = cursor.fetchone()
        if row:
            logger.info(f"Retrieved student with ID: {id}")
            return jsonify(row)
        else:
            logger.warning(f"Student with ID: {id} not found.")
            return jsonify({'message': 'Student not found'}), 404
    except Error as e:
        logger.error(f"Error fetching student with ID {id}: {e}")
        return jsonify({'message': 'Error fetching student', 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed.")


# Create Student
@app.route('/students', methods=['POST'])
def create_student():
    """Creates a new student record."""
    data = request.json
    name = data.get('name')
    age = data.get('age')

    if not name or not age:
        logger.warning("Missing name or age for new student creation.")
        return jsonify({'message': 'Name and age are required'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO students (name, age) VALUES (%s, %s)', (name, age))
        conn.commit()
        new_student_id = cursor.lastrowid
        logger.info(f"Student '{name}' created successfully with ID: {new_student_id}")
        # Return the created student's ID for immediate feedback
        return jsonify({'message': 'Student created successfully', 'id': new_student_id, 'name': name, 'age': age}), 201
    except Error as e:
        conn.rollback() # Rollback on error
        logger.error(f"Error creating student '{name}': {e}")
        return jsonify({'message': 'Error creating student', 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed.")


# Update Student
@app.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    """Updates an existing student record."""
    data = request.json
    name = data.get('name')
    age = data.get('age')

    if not name and not age: # Allow partial updates, but require at least one field
        logger.warning(f"No update data provided for student ID: {id}")
        return jsonify({'message': 'No data provided for update'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        if name is not None: # Allow updating to empty string if desired
            updates.append('name=%s')
            params.append(name)
        if age is not None:
            updates.append('age=%s')
            params.append(age)

        if not updates: # Should be caught by earlier check, but good double-check
            return jsonify({'message': 'No valid fields to update'}), 400

        params.append(id) # Add ID for WHERE clause
        query = f'UPDATE students SET {", ".join(updates)} WHERE id=%s'
        cursor.execute(query, tuple(params))
        conn.commit()

        if cursor.rowcount == 0:
            logger.warning(f"Attempted to update student ID {id}, but student not found.")
            return jsonify({'message': 'Student not found or no changes made'}), 404
        else:
            logger.info(f"Student with ID {id} updated successfully.")
            return jsonify({'message': 'Student updated successfully'})
    except Error as e:
        conn.rollback()
        logger.error(f"Error updating student ID {id}: {e}")
        return jsonify({'message': 'Error updating student', 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed.")


# Delete Student
@app.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    """Deletes a student record by ID."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE id = %s', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(f"Attempted to delete student ID {id}, but student not found.")
            return jsonify({'message': 'Student not found'}), 404
        else:
            logger.info(f"Student with ID {id} deleted successfully.")
            return jsonify({'message': 'Student deleted successfully'})
    except Error as e:
        conn.rollback()
        logger.error(f"Error deleting student ID {id}: {e}")
        return jsonify({'message': 'Error deleting student', 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed.")

# Run the Flask App
if __name__ == '__main__':
    # Use this for local development only.
    # For production, use a WSGI server like Gunicorn (e.g., gunicorn -w 4 -b 0.0.0.0:5000 app:app)
    logger.info("Starting Flask application in development mode...")
    app.run(debug=True, host='0.0.0.0', port=5000) 