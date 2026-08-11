
import os
import json
import psycopg2
from psycopg2.extras import Json


# =========================================================
# DATABASE CONNECTION
# =========================================================

DATABASE = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:intern@13.92.101.67:5432/postgres"
)


def get_connection():

    return psycopg2.connect(
        DATABASE
    )


# =========================================================
# SCHEMA DIRECTORY
# =========================================================

def get_schemas_directory():

    # db.py is inside:
    #
    # backend/app/db.py
    #
    # So schemas is:
    #
    # backend/app/schemas/

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    return os.path.join(
        base_dir,
        "schemas"
    )


# =========================================================
# REGISTER JSON FORMS IN DATABASE
# =========================================================

def register_schemas():

    schemas_dir = get_schemas_directory()

    if not os.path.exists(schemas_dir):

        print(
            f"[WARNING] Schemas directory not found: "
            f"{schemas_dir}"
        )

        return

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            # ---------------------------------------------
            # Find every JSON file
            # ---------------------------------------------

            for filename in os.listdir(schemas_dir):

                if not filename.endswith(".json"):
                    continue

                filepath = os.path.join(
                    schemas_dir,
                    filename
                )

                try:

                    with open(
                        filepath,
                        "r",
                        encoding="utf-8"
                    ) as file:

                        schema = json.load(file)

                except Exception as e:

                    print(
                        f"[SCHEMA ERROR] Could not load "
                        f"{filename}: {e}"
                    )

                    continue

                # -----------------------------------------
                # Make sure schema is a JSON object
                # -----------------------------------------

                if not isinstance(schema, dict):

                    print(
                        f"[SCHEMA ERROR] {filename} "
                        f"must contain a JSON object."
                    )

                    continue

                # -----------------------------------------
                # Get form ID dynamically
                #
                # If JSON contains:
                #
                # "form_id": "employee_form"
                #
                # use that.
                #
                # Otherwise:
                #
                # employee_form.json
                #
                # becomes:
                #
                # employee_form
                # -----------------------------------------

                form_id = schema.get(
                    "form_id"
                )

                if not form_id:

                    form_id = os.path.splitext(
                        filename
                    )[0]

                # -----------------------------------------
                # Get display name dynamically
                # -----------------------------------------

                form_name = schema.get(
                    "form_name",
                    form_id
                )

                # -----------------------------------------
                # Insert or update the form
                # -----------------------------------------

                cursor.execute(
                    """
                    INSERT INTO form_schema
                    (
                        form_id,
                        form_name,
                        json_schema
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )

                    ON CONFLICT(form_id)
                    DO UPDATE SET
                        form_name = EXCLUDED.form_name,
                        json_schema = EXCLUDED.json_schema
                    """,
                    (
                        form_id,
                        form_name,
                        Json(schema)
                    )
                )

                print(
                    f"[SCHEMA REGISTERED] {form_id}"
                )

        conn.commit()

    finally:

        conn.close()


# =========================================================
# INITIALIZE TABLES
# =========================================================

def init_tables():

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
                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,

                    form_id VARCHAR(255) NOT NULL,

                    status VARCHAR(50)
                        DEFAULT 'COLLECTING',

                    current_state JSONB
                        DEFAULT '{}'::jsonb,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_form
                    FOREIGN KEY(form_id)
                    REFERENCES form_schema(form_id)
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id UUID PRIMARY KEY
                        DEFAULT gen_random_uuid(),

                    session_id VARCHAR(255) NOT NULL,

                    submitted_data JSONB NOT NULL,

                    submitted_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_session
                    FOREIGN KEY(session_id)
                    REFERENCES conversation_sessions(session_id)
                    ON DELETE CASCADE
                );
                """
            )

        conn.commit()

    finally:

        conn.close()

    # =====================================================
    # IMPORTANT
    #
    # Tables must exist BEFORE registering forms because
    # register_schemas() inserts into form_schema.
    # =====================================================

    register_schemas()


# =========================================================
# GET SAVED CONVERSATION
# =========================================================

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


# =========================================================
# SAVE CONVERSATION
# =========================================================

def save_conversation(
    session_id,
    form_id,
    current_state
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO conversation_sessions
                (
                    session_id,
                    form_id,
                    current_state,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'COLLECTING'
                )

                ON CONFLICT(session_id)
                DO UPDATE SET
                    current_state =
                        EXCLUDED.current_state,

                    status =
                        'COLLECTING',

                    updated_at =
                        CURRENT_TIMESTAMP
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


# =========================================================
# SAVE COMPLETED SUBMISSION
# =========================================================

def save_submission(
    session_id,
    
    submitted_data
):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

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

            cursor.execute(
                """
                UPDATE conversation_sessions

                SET
                    status = 'COMPLETED',

                    current_state = %s,

                    updated_at =
                        CURRENT_TIMESTAMP

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


# =========================================================
# BACKWARD-COMPATIBILITY ALIAS
# =========================================================
#
# Your current main.py imports:
#
#     save_submissions
#
# while your original db.py defines:
#
#     save_submission
#
# This alias allows both names to work.
#
# =========================================================

save_submissions = save_submission

