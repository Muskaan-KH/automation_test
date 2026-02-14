import json
import os
from datetime import datetime
from config import DB_PATH

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.data = {
            'users': {},
            'total_users': 0,
            'settings': {}
        }
        self.load()

    def load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                print("Error decoding JSON, starting fresh.")
                self.save()
        else:
            self.save()

    def save(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def add_user(self, chat_id, first_name, username, referred_by=None):
        str_chat_id = str(chat_id)
        
        if str_chat_id not in self.data['users']:
            self.data['users'][str_chat_id] = {
                'chat_id': str_chat_id,
                'first_name': first_name,
                'username': username,
                'joined_at': str(datetime.now()),
                'referred_by': referred_by,
                'referrals': 0,
                'last_active': str(datetime.now()),
                'status': 'active',
                'messages_sent': []
            }
            self.data['total_users'] += 1
            
            # Update referrer stats if applicable
            if referred_by and referred_by in self.data['users']:
                self.data['users'][referred_by]['referrals'] += 1
                
            self.save()
            return self.data['users'][str_chat_id]
        
        return self.data['users'][str_chat_id]

    def get_user(self, chat_id):
        return self.data['users'].get(str(chat_id))

    def update_last_active(self, chat_id):
        str_chat_id = str(chat_id)
        if str_chat_id in self.data['users']:
            self.data['users'][str_chat_id]['last_active'] = str(datetime.now())
            self.save()

    def get_active_users(self, limit=100):
        # Return users sorted by last_active (just a simple implementation for now)
        users = list(self.data['users'].values())
        # Filter strictly active if needed, currently just returning top N
        return users[:limit]

    def get_all_users(self):
        return self.data['users']

    def log_message_sent(self, chat_id, message_type):
        str_chat_id = str(chat_id)
        if str_chat_id in self.data['users']:
            if 'messages_sent' not in self.data['users'][str_chat_id]:
                self.data['users'][str_chat_id]['messages_sent'] = []
            
            self.data['users'][str_chat_id]['messages_sent'].append({
                'type': message_type,
                'timestamp': str(datetime.now())
            })
            self.save()

# Create global instance
db = Database(DB_PATH)