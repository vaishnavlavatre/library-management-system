from flask import Flask, request, jsonify
import sqlite3
import requests
import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('books_db.sqlite')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT NOT NULL,
                 author TEXT NOT NULL,
                 quantity INTEGER NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS borrow_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 book_id INTEGER NOT NULL,
                 user_id INTEGER NOT NULL,
                 borrow_date TEXT NOT NULL,
                 return_date TEXT,
                 FOREIGN KEY(book_id) REFERENCES books(id))''')
    
    # Add some sample books if none exist
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', 5),
            ('To Kill a Mockingbird', 'Harper Lee', 3),
            ('1984', 'George Orwell', 4)
        ]
        c.executemany("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)", sample_books)
    
    conn.commit()
    conn.close()

init_db()

# Helper function to verify JWT token
def verify_token(token):
    if not token:
        return None
    
    try:
        auth_service_url = "http://auth_service:5000/verify"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(auth_service_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error verifying token: {e}")
        return None
    
    return None

@app.route('/books', methods=['GET'])
def get_books():
    try:
        conn = sqlite3.connect('books_db.sqlite')
        c = conn.cursor()
        c.execute("SELECT * FROM books")
        books = [{'id': row[0], 'title': row[1], 'author': row[2], 'quantity': row[3]} for row in c.fetchall()]
        conn.close()
        return jsonify(books), 200
    except Exception as e:
        app.logger.error(f"Error fetching books: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.get_json()
    book_id = data.get('book_id')
    user_id = data.get('user_id')
    
    if not book_id or not user_id:
        return jsonify({'message': 'Book ID and User ID are required!'}), 400
    
    token = request.headers.get('Authorization')
    if not token or not verify_token(token.split()[1]):
        return jsonify({'message': 'Invalid or missing token!'}), 401
    
    try:
        conn = sqlite3.connect('books_db.sqlite')
        c = conn.cursor()
        
        # Check book availability
        c.execute("SELECT quantity FROM books WHERE id=?", (book_id,))
        result = c.fetchone()
        if not result or result[0] <= 0:
            conn.close()
            return jsonify({'message': 'Book not available for borrowing!'}), 400
        
        # Update book quantity
        c.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?", (book_id,))
        
        # Create borrow record
        borrow_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO borrow_records (book_id, user_id, borrow_date) VALUES (?, ?, ?)",
                  (book_id, user_id, borrow_date))
        
        conn.commit()
        conn.close()
        
        # Notify notification service
        notification_data = {
            'user_id': user_id,
            'message': f'You have successfully borrowed book ID {book_id}',
            'notification_type': 'borrow'
        }
        try:
            response = requests.post(
                'http://notification_service:5002/notify',
                  json=notification_data, headers={'Authorization': token})
            if response.status_code != 201:
                app.logger.warning(f"Notification service responded with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error notifying notification service: {e}")
        
        return jsonify({'message': 'Book borrowed successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error borrowing book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/return', methods=['POST'])
def return_book():
    data = request.get_json()
    book_id = data.get('book_id')
    user_id = data.get('user_id')
    
    if not book_id or not user_id:
        return jsonify({'message': 'Book ID and User ID are required!'}), 400
    
    token = request.headers.get('Authorization')
    if not token or not verify_token(token.split()[1]):
        return jsonify({'message': 'Invalid or missing token!'}), 401
    
    try:
        conn = sqlite3.connect('books_db.sqlite')
        c = conn.cursor()
        
        # Find active borrow record
        c.execute("SELECT id FROM borrow_records WHERE book_id=? AND user_id=? AND return_date IS NULL",
                  (book_id, user_id))
        record = c.fetchone()
        
        if not record:
            conn.close()
            return jsonify({'message': 'No active borrow record found!'}), 400
        
        # Update book quantity
        c.execute("UPDATE books SET quantity = quantity + 1 WHERE id=?", (book_id,))
        
        # Update borrow record with return date
        return_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE borrow_records SET return_date=? WHERE id=?", (return_date, record[0]))
        
        conn.commit()
        conn.close()
        
        # Notify notification service
        notification_data = {
            'user_id': user_id,
            'message': f'You have successfully returned book ID {book_id}',
            'notification_type': 'return'
        }
        try:
            response = requests.post('http://notification_service:5002/notify', json=notification_data, headers={'Authorization': token})
            if response.status_code != 201:
                app.logger.warning(f"Notification service responded with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error notifying notification service: {e}")
        
        return jsonify({'message': 'Book returned successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error returning book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/borrow_status', methods=['GET'])
def borrow_status():
    try:
        conn = sqlite3.connect('books_db.sqlite')
        c = conn.cursor()

        # Query to get the borrowing status of all books
        c.execute('''
            SELECT b.id, b.title, b.author, COUNT(br.id) AS borrowers_count
            FROM books b
            LEFT JOIN borrow_records br ON b.id = br.book_id AND br.return_date IS NULL
            GROUP BY b.id, b.title, b.author
        ''')
        status = [
            {
                'book_id': row[0],
                'title': row[1],
                'author': row[2],
                'borrowers_count': row[3]
            }
            for row in c.fetchall()
        ]

        conn.close()
        return jsonify(status), 200
    except Exception as e:
        app.logger.error(f"Error fetching borrow status: {e}")
        return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)