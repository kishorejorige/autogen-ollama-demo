import os

# Ensure all tests use an in-memory SQLite database to prevent touching production database files
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
