from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('notification_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 message TEXT NOT NULL,
                 notification_type TEXT NOT NULL,
                 created_at TEXT NOT NULL,
                 is_read INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/notify', methods=['POST'])
def create_notification():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    notification_type = data.get('notification_type')
    
    if not all([user_id, message, notification_type]):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    conn = sqlite3.connect('notification_db.sqlite')
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO notifications (user_id, message, notification_type, created_at) VALUES (?, ?, ?, ?)",
              (user_id, message, notification_type, created_at))
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notification created successfully!'}), 201

@app.route('/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    #print method entry
    print(f"Fetching notifications for user_id: {user_id}")
    conn = sqlite3.connect('notification_db.sqlite')
    c = conn.cursor()
    
    c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    notifications = [{
        'id': row[0],
        'message': row[2],
        'type': row[3],
        'created_at': row[4],
        'is_read': bool(row[5])
    } for row in c.fetchall()]
    
    # Mark as read
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify(notifications)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)