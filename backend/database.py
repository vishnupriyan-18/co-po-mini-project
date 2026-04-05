"""Database Helper Module"""
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'marks.db')

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    """Initialize database with schema"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')
    
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    conn = get_db_connection()
    try:
        conn.executescript(schema)
        conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

def execute_query(query, params=(), fetch_one=False):
    """Execute SELECT query"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, params)
        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else None
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def execute_insert(query, params=()):
    """Execute INSERT query and return last row id"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def execute_update(query, params=()):
    """Execute UPDATE or DELETE query"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
