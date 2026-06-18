import psycopg2
from config import get_connection

def init_db():
    """Applies schema definition and ensures a default Master PIN exists."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        with open("schema.sql", "r") as f:
            schema_sql = f.read()
            cur.execute(schema_sql)
        
        cur.execute("SELECT value FROM app_settings WHERE key = 'master_pin';")
        if not cur.fetchone():
            cur.execute("INSERT INTO app_settings (key, value) VALUES ('master_pin', '1234');")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_master_pin() -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = 'master_pin';")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else "1234"

def update_master_pin(new_pin: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE app_settings SET value = %s WHERE key = 'master_pin';", (new_pin,))
    conn.commit()
    cur.close()
    conn.close()

# Users Query Functions
def add_user(username: str, email: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email) VALUES (%s, %s) ON CONFLICT (username) DO UPDATE SET email = EXCLUDED.email RETURNING id;",
        (username, email)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return user_id

def get_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users ORDER BY username ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_user(user_id: int, username: str, email: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s;", (username, email, user_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

# Password Types Query Functions
def add_password_type(name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO password_types (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id;",
        (name,)
    )
    type_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return type_id

def get_password_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM password_types ORDER BY name ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_password_type(type_id: int, name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE password_types SET name = %s WHERE id = %s;", (name, type_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_password_type(type_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_types WHERE id = %s;", (type_id,))
    conn.commit()
    cur.close()
    conn.close()

# Password Sub-types Query Functions
def add_password_subtype(type_id: int, name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO password_subtypes (type_id, name) VALUES (%s, %s) 
           ON CONFLICT (type_id, name) DO UPDATE SET name = EXCLUDED.name RETURNING id;""",
        (type_id, name)
    )
    subtype_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return subtype_id

def get_password_subtypes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pst.id, pst.type_id, pt.name as type_name, pst.name as subtype_name 
        FROM password_subtypes pst
        JOIN password_types pt ON pst.type_id = pt.id
        ORDER BY pt.name, pst.name ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_subtypes_by_type(type_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM password_subtypes WHERE type_id = %s ORDER BY name ASC;", (type_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_password_subtype(subtype_id: int, type_id: int, name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE password_subtypes SET type_id = %s, name = %s WHERE id = %s;", (type_id, name, subtype_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_password_subtype(subtype_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_subtypes WHERE id = %s;", (subtype_id,))
    conn.commit()
    cur.close()
    conn.close()

# Password Credentials Table Functions
def add_password(user_id: int, type_id: int, subtype_id: int, title: str, username_or_email: str, encrypted_val: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO passwords (user_id, type_id, subtype_id, title, username_or_email, encrypted_password)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (user_id, type_id, subtype_id, title, username_or_email, encrypted_val))
    conn.commit()
    cur.close()
    conn.close()

def get_passwords():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, u.username, pt.name as type_name, pst.name as subtype_name, 
               p.title, p.username_or_email, p.encrypted_password, p.user_id, p.type_id, p.subtype_id
        FROM passwords p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN password_types pt ON p.type_id = pt.id
        LEFT JOIN password_subtypes pst ON p.subtype_id = pst.id
        ORDER BY p.title ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_passwords_by_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, u.username, pt.name as type_name, pst.name as subtype_name, 
               p.title, p.username_or_email, p.encrypted_password, p.user_id, p.type_id, p.subtype_id
        FROM passwords p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN password_types pt ON p.type_id = pt.id
        LEFT JOIN password_subtypes pst ON p.subtype_id = pst.id
        WHERE p.user_id = %s
        ORDER BY p.title ASC;
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_password(pass_id: int, user_id: int, type_id: int, subtype_id: int, title: str, username_or_email: str, encrypted_val: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE passwords 
        SET user_id = %s, type_id = %s, subtype_id = %s, title = %s, username_or_email = %s, encrypted_password = %s
        WHERE id = %s;
    """, (user_id, type_id, subtype_id, title, username_or_email, encrypted_val, pass_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_password(pass_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM passwords WHERE id = %s;", (pass_id,))
    conn.commit()
    cur.close()
    conn.close()

def clear_all_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE passwords, password_subtypes, password_types, users RESTART IDENTITY CASCADE;")
    conn.commit()
    cur.close()
    conn.close()