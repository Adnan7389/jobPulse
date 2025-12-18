import os
import sys

# Add parent directory to path if needed, or handle via docker path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BACKEND_URL = os.getenv("BACKEND_URL", "http://web:8000")

# Security & Compliance: Blocked channels (comma-separated usernames)
DENYLIST = set(filter(None, [u.strip() for u in os.getenv("DENYLIST", "").split(",")]))

if not API_ID or not API_HASH:
    print("Error: API_ID and API_HASH must be set in environment variables.")
    sys.exit(1)

# Ensure integer
try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: API_ID must be an integer.")
    sys.exit(1)
