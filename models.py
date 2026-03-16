from flask_login import UserMixin
from database import get_db
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.role = user_data['role']  # 'admin' or 'teacher'
        self.name = user_data.get('name', '')

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None

    @staticmethod
    def get_by_username(username):
        db = get_db()
        user_data = db.users.find_one({'username': username})
        if user_data:
            return User(user_data), user_data.get('password')
        return None, None
