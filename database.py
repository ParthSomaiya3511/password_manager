import psycopg2
from config import get_connection

def init_db():
    """Initializes schema and runs primary-key-safe table migrations dynamically."""
    
    def run_query(sql, params=None):
        """Helper to run a query in an isolated connection transaction."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    # 1. Ensure basic tables exist
    run_query("CREATE TABLE IF NOT EXISTS app_settings (key VARCHAR(50) PRIMARY KEY, value VARCHAR(255) NOT NULL);")
    run_query("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(100) UNIQUE NOT NULL, email VARCHAR(255) NOT NULL);")
    run_query("CREATE TABLE IF NOT EXISTS password_types (name VARCHAR(100) NOT NULL);")
    run_query("CREATE TABLE IF NOT EXISTS password_subtypes (name VARCHAR(100) NOT NULL);")
    run_query("CREATE TABLE IF NOT EXISTS passwords (title VARCHAR(255) NOT NULL, username_or_email VARCHAR(255) NOT NULL, encrypted_password TEXT NOT NULL);")

    # 2. Dynamic schema migrations (Committed individually with PK-clash checks)
    # password_types
    run_query("ALTER TABLE password_types ADD COLUMN IF NOT EXISTS user_id INT REFERENCES users(id) ON DELETE CASCADE;")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT tc.constraint_name FROM information_schema.table_constraints tc WHERE tc.table_name = 'password_types' AND tc.constraint_type = 'PRIMARY KEY';")
        has_pk = cur.fetchone() is not None
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='password_types' AND column_name='id';")
        has_id = cur.fetchone() is not None
        if not has_id:
            if not has_pk:
                cur.execute("ALTER TABLE password_types ADD COLUMN id SERIAL PRIMARY KEY;")
            else:
                cur.execute("ALTER TABLE password_types ADD COLUMN id SERIAL;")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    # Repair legacy constraints on password_types
    run_query("ALTER TABLE password_types DROP CONSTRAINT IF EXISTS password_types_user_id_fkey;")
    run_query("ALTER TABLE password_types ADD CONSTRAINT password_types_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    run_query("ALTER TABLE password_types DROP CONSTRAINT IF EXISTS unique_user_type;")
    run_query("ALTER TABLE password_types ADD CONSTRAINT unique_user_type UNIQUE (user_id, name);")

    # password_subtypes
    run_query("ALTER TABLE password_subtypes ADD COLUMN IF NOT EXISTS user_id INT REFERENCES users(id) ON DELETE CASCADE;")
    run_query("ALTER TABLE password_subtypes ADD COLUMN IF NOT EXISTS type_id INT REFERENCES password_types(id) ON DELETE CASCADE;")
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT tc.constraint_name FROM information_schema.table_constraints tc WHERE tc.table_name = 'password_subtypes' AND tc.constraint_type = 'PRIMARY KEY';")
        has_pk = cur.fetchone() is not None
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='password_subtypes' AND column_name='id';")
        has_id = cur.fetchone() is not None
        if not has_id:
            if not has_pk:
                cur.execute("ALTER TABLE password_subtypes ADD COLUMN id SERIAL PRIMARY KEY;")
            else:
                cur.execute("ALTER TABLE password_subtypes ADD COLUMN id SERIAL;")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    # Repair legacy constraints on password_subtypes
    run_query("ALTER TABLE password_subtypes DROP CONSTRAINT IF EXISTS password_subtypes_user_id_fkey;")
    run_query("ALTER TABLE password_subtypes ADD CONSTRAINT password_subtypes_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    run_query("ALTER TABLE password_subtypes DROP CONSTRAINT IF EXISTS unique_type_subtype;")
    run_query("ALTER TABLE password_subtypes ADD CONSTRAINT unique_type_subtype UNIQUE (type_id, name);")

    # passwords columns dynamic migrations
    run_query("ALTER TABLE passwords ADD COLUMN IF NOT EXISTS user_id INT REFERENCES users(id) ON DELETE CASCADE;")
    run_query("ALTER TABLE passwords ADD COLUMN IF NOT EXISTS type_id INT REFERENCES password_types(id) ON DELETE SET NULL;")
    run_query("ALTER TABLE passwords ADD COLUMN IF NOT EXISTS subtype_id INT REFERENCES password_subtypes(id) ON DELETE SET NULL;")
    run_query("ALTER TABLE passwords ADD COLUMN IF NOT EXISTS title VARCHAR(255);")
    run_query("ALTER TABLE passwords ADD COLUMN IF NOT EXISTS username_or_email VARCHAR(255);")
    run_query("ALTER TABLE passwords ADD COLUMN IF NOT EXISTS encrypted_password TEXT;")

    # Drop old legacy constraints pointing to 'users_master', 'password_type_master', and 'password_subtype_master'
    run_query("ALTER TABLE passwords DROP CONSTRAINT IF EXISTS passwords_user_id_fkey;")
    run_query("ALTER TABLE passwords DROP CONSTRAINT IF EXISTS passwords_type_id_fkey;")
    run_query("ALTER TABLE passwords DROP CONSTRAINT IF EXISTS passwords_subtype_id_fkey;")

    # Re-add correct foreign keys
    run_query("ALTER TABLE passwords ADD CONSTRAINT passwords_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
    run_query("ALTER TABLE passwords ADD CONSTRAINT passwords_type_id_fkey FOREIGN KEY (type_id) REFERENCES password_types(id) ON DELETE SET NULL;")
    run_query("ALTER TABLE passwords ADD CONSTRAINT passwords_subtype_id_fkey FOREIGN KEY (subtype_id) REFERENCES password_subtypes(id) ON DELETE SET NULL;")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if table passwords already has a primary key
        cur.execute("SELECT tc.constraint_name FROM information_schema.table_constraints tc WHERE tc.table_name = 'passwords' AND tc.constraint_type = 'PRIMARY KEY';")
        has_pk_passwords = cur.fetchone() is not None
        
        # Check if column 'id' exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='passwords' AND column_name='id';")
        has_id_column = cur.fetchone() is not None
        
        if not has_id_column:
            if not has_pk_passwords:
                cur.execute("ALTER TABLE passwords ADD COLUMN id SERIAL PRIMARY KEY;")
            else:
                cur.execute("ALTER TABLE passwords ADD COLUMN id SERIAL;")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def is_pin_configured() -> bool:
    """Checks if a Master PIN is configured inside the database app_settings table."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM app_settings WHERE key = 'master_pin';")
        row = cur.fetchone()
        return (row is not None and row[0] != "")
    except Exception:
        return False
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
    return row[0] if row else ""

def update_master_pin(new_pin: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM app_settings WHERE key = 'master_pin';")
    cur.execute("INSERT INTO app_settings (key, value) VALUES ('master_pin', %s);", (new_pin,))
    conn.commit()
    cur.close()
    conn.close()

def set_initial_pin(pin: str):
    """Sets the initial Master PIN in the database."""
    update_master_pin(pin)

# Dynamic ID Resolution Functions (Bypasses stale Streamlit indexes)
def get_user_id_by_name(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s;", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_type_id_by_name(user_id: int, name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM password_types WHERE user_id = %s AND name = %s;", (user_id, name))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_subtype_id_by_name(type_id: int, name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM password_subtypes WHERE type_id = %s AND name = %s;", (type_id, name))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

# Users Table Functions
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

# Category Types Scoped by User
def add_password_type(user_id: int, name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO password_types (user_id, name) VALUES (%s, %s) 
           ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name RETURNING id;""",
        (user_id, name)
    )
    type_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return type_id

def get_password_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pt.id, pt.user_id, u.username, pt.name 
        FROM password_types pt
        JOIN users u ON pt.user_id = u.id
        ORDER BY u.username, pt.name ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_password_types_by_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM password_types WHERE user_id = %s ORDER BY name ASC;", (user_id,))
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

# Sub-types Scoped by User & Parent Type
def add_password_subtype(user_id: int, type_id: int, name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO password_subtypes (user_id, type_id, name) VALUES (%s, %s, %s) 
           ON CONFLICT (type_id, name) DO UPDATE SET name = EXCLUDED.name RETURNING id;""",
        (user_id, type_id, name)
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
        SELECT pst.id, pst.user_id, u.username, pst.type_id, pt.name as type_name, pst.name as subtype_name 
        FROM password_subtypes pst
        JOIN users u ON pst.user_id = u.id
        JOIN password_types pt ON pst.type_id = pt.id
        ORDER BY u.username, pt.name, pst.name ASC;
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