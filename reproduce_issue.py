
class DatabaseMock:
    def __init__(self):
        self.data = {
            'users': {
                '123': 5  # Simulating an integer where a dict should be
            }
        }

    def log_message_sent(self, chat_id):
        str_chat_id = str(chat_id)
        print(f"Checking if {str_chat_id} in users...")
        if str_chat_id in self.data['users']:
            print("Found user.")
            try:
                print("Checking 'messages_sent' in user...")
                if 'messages_sent' not in self.data['users'][str_chat_id]:
                    print("Initializing messages_sent...")
                    self.data['users'][str_chat_id]['messages_sent'] = []
            except Exception as e:
                print(f"Line 78 equivalent failed with: {e}")

            try:
                print("Appending to messages_sent...")
                self.data['users'][str_chat_id]['messages_sent'].append({})
            except Exception as e:
                print(f"Line 81 equivalent failed with: {e}")

db = DatabaseMock()
db.log_message_sent(123)
