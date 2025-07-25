import os
import redis
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# Load .env relative to BASE_DIR, just like in your settings
load_dotenv(dotenv_path=BASE_DIR / '.env', override=True)

# Get the MODE variable
MODE = os.getenv("MODE", "development").lower()

final_redis_url = ''

if MODE == "production":
    final_redis_url = os.getenv('REDIS_URL', os.getenv('REDIS_URL_PROD'))
    if not final_redis_url:
        print("ERROR: In production mode, REDIS_URL or REDIS_URL_PROD must be set in .env")
        exit(1)
else: # development
    final_redis_url = os.getenv('REDIS_URL_DEV', 'redis://localhost:6379/') # Fallback to localhost if not in .env

print(f"Loading settings in MODE: {MODE}")
print(f"Attempting to connect to Redis at: {final_redis_url}")

try:
    # Use redis.from_url to handle 'redis://' or 'rediss://' (for SSL)
    # decode_responses=True ensures that Redis responses are Python strings
    r = redis.from_url(final_redis_url, decode_responses=True)

    # Attempt to ping the Redis server
    response = r.ping()
    if response:
        print("SUCCESS: Connected to Redis! Ping responded with:", response)
        # Optional: Set and get a key to verify write/read
        r.set('test_key', 'Hello Redis!')
        value = r.get('test_key')
        print(f"Key 'test_key' set and read: {value}")
        r.delete('test_key') # Clean up
    else:
        print("WARNING: Connected to Redis, but ping failed.")

except redis.exceptions.ConnectionError as e:
    print(f"ERROR: Could not connect to Redis. Details: {e}")
    print("Please ensure the Redis server is running and accessible at the provided URL.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")