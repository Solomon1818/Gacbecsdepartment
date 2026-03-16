"""
Run this script ONCE to create your first admin and teacher accounts.
Usage: python seed_users.py
"""
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.environ.get('MONGO_URI'))
db = client[os.environ.get('DB_NAME', 'student_db')]

def create_user(username, password, role, name):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    existing = db.users.find_one({'username': username})
    if existing:
        print(f"User '{username}' already exists. Skipping.")
        return
    db.users.insert_one({
        'username': username,
        'password': hashed,
        'role': role,
        'name': name
    })
    print(f"Created {role}: {username}")

if __name__ == '__main__':
    # Create admin account
    create_user(
        username='admin',
        password='admin123',     # Change this!
        role='admin',
        name='Admin'
    )
    # Create a teacher account
    create_user(
        username='teacher1',
        password='teacher123',   # Change this!
        role='teacher',
        name='Teacher One'
    )
    print("\nDone! Please change the passwords after first login.")
    print("Login at: http://localhost:5000/login")
