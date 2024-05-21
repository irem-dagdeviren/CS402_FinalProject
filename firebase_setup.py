import firebase_admin
from firebase_admin import credentials, db

def init_firebase():
    cred = credentials.Certificate('credentials.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cs402-1c97e-default-rtdb.europe-west1.firebasedatabase.app'  # Replace with your database URL
    })
