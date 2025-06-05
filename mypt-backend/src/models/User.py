from src.config.db import get_mongo_collection  # 경로 수정

class User:
    def __init__(self, email, password_hash):
        self.email = email
        self.password = password_hash
        self.collection = get_mongo_collection('users')

    def save(self):
        user_data = {
            'email': self.email,
            'password': self.password
        }
        return self.collection.insert_one(user_data)

    @staticmethod
    def find_by_email(email):
        collection = get_mongo_collection('users')
        return collection.find_one({'email': email})
