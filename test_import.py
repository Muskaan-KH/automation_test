import config
import database
import os

print(f"Config Import Successful. DB_PATH: {config.DB_PATH}")
print(f"Database Import Successful. Connection function: {database.get_db_connection}")

if os.path.exists(config.DB_PATH):
    print("Database file exists.")
else:
    print("Database file does not exist yet (will be created on init).")
