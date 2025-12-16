#!/usr/bin/env python3
"""
Database initialization script for the RAG backend.
This script creates all required tables in the database.
"""

import os
import sys
from sqlalchemy import create_engine
from database.models import Base
from rag_agent.config import validate_environment

def init_db():
    """Initialize the database by creating all tables."""
    print("Validating environment variables...")
    is_valid, missing_vars = validate_environment()
    if not is_valid:
        print(f"Error: Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Get database URL from environment
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        print("Error: NEON_DATABASE_URL environment variable is not set")
        sys.exit(1)

    print(f"Connecting to database: {database_url}")

    try:
        # Create engine
        engine = create_engine(database_url)

        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables created: {tables}")

        return True

    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = init_db()
    if success:
        print("Database initialization completed successfully!")
        sys.exit(0)
    else:
        print("Database initialization failed!")
        sys.exit(1)