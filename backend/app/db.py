import json
import os
import psycopg2
from psycopg2.extras import Json

# PostgreSQL connection string
DATABASE = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:intern@13.92.101.67:5432/postgres"
)

# Connect Flask to PostgreSQL
def get_connection():
    return psycopg2.connect(DATABASE)


# Initialize database tables
# Initialize database tables
def init_tables():
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE EXTENSION IF NOT EXISTS pgcrypto;

                    CREATE TABLE IF NOT EXISTS form_schema (
                        form_id VARCHAR(255) PRIMARY KEY,
                        form_name VARCHAR(255) NOT NULL,
                        json_schema JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS conversation_sessions (
                        session_id VARCHAR(255) PRIMARY KEY,
                        form_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) DEFAULT 'COLLECTING',
                        current_state JSONB DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    );

                    CREATE TABLE IF NOT EXISTS submissions (
                        submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id VARCHAR(255) NOT NULL,
                        submitted_data JSONB NOT NULL,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                        CONSTRAINT fk_session
                        FOREIGN KEY(session_id)
                        REFERENCES conversation_sessions(session_id)
                        ON DELETE CASCADE
                    );

                    INSERT INTO form_schema (form_id, form_name, json_schema)
                    VALUES (
                        'user_registration', 
                        'User Registration', 
                        '{"fields": {"first_name": {"type": "string", "required": true}, "last_name": {"type": "string", "required": true}, "email": {"type": "email", "required": true}}}'::jsonb
                    )
                    ON CONFLICT (form_id) DO NOTHING;
                    """
                )
                conn.commit()
        finally:
            conn.close()
    except psycopg2.OperationalError as e:
        print(f"[WARNING] Database connection skipped during startup: {e}")
# Load form schema
def load_form_schema_from_db(form_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT json_schema
                FROM form_schema
                WHERE form_id = %s
                """,
                (form_id,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            return {}
    finally:
        conn.close()


# Retrieve saved conversation state
def get_saved_conversation(session_id):
    conn = get_connection()
    try:  
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT current_state
                FROM conversation_sessions
                WHERE session_id = %s
                """,
                (session_id,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            return {}
    finally:
        conn.close()


# Save or update conversation progress
def save_conversation(session_id, form_id, current_state):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO form_schema (form_id, form_name, json_schema)
                VALUES (%s, %s, %s)
                ON CONFLICT (form_id) DO NOTHING;
                """,
                (form_id, form_id.replace('_', ' ').title(), Json({}))
            )
            cursor.execute(
                """
                INSERT INTO conversation_sessions
                (
                    session_id,
                    form_id,
                    current_state,
                    status
                )
                VALUES (%s, %s, %s, 'COLLECTING')

                ON CONFLICT(session_id)
                DO UPDATE SET
                    form_id = EXCLUDED.form_id,
                    current_state = EXCLUDED.current_state,
                    status = 'COLLECTING',
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    session_id,
                    form_id,
                    Json(current_state)
                )
            )
            conn.commit()
    finally:
        conn.close()


# Save completed form submission
def save_submissions(session_id, form_id, submitted_data):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Insert into submissions
            cursor.execute(
                """
                INSERT INTO submissions
                (
                    session_id,
                    submitted_data
                )
                VALUES (%s, %s)
                """,
                (
                    session_id,
                    Json(submitted_data)
                )
            )

            # 2. Mark session status as COMPLETED
            cursor.execute(
                """
                UPDATE conversation_sessions
                SET status = 'COMPLETED',
                    current_state = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
                """,
                (
                    Json(submitted_data),
                    session_id
                )
            )
            conn.commit()
    finally:
        conn.close()