# ✅ Updated database.py
import mysql.connector
from mysql.connector import Error
import bcrypt

class Database:
    def __init__(self):
        self.conn = self.connect()

    def connect(self):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                port=3307,
                user="root",
                password="5218kaviya",
                database="memory_assistant1"
            )
            return conn
        except Error as e:
            print("❌ Database connection failed:", e)
            return None

    def get_user(self, username):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()
        finally:
            conn.close()

    def create_user(self, username, password):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            return True
        except mysql.connector.IntegrityError:
            return False
        finally:
            conn.close()

    def link_family_member(self, user_id, fam_username):
        conn = self.connect()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (fam_username,))
            fam_id = cursor.fetchone()
            if not fam_id:
                return False
            fam_id = fam_id[0]
            cursor.execute("SELECT COUNT(*) FROM family_links WHERE user_id = %s AND family_id = %s", (user_id, fam_id))
            if cursor.fetchone()[0] > 0:
                return False
            cursor.execute("INSERT INTO family_links (user_id, family_id) VALUES (%s, %s)", (user_id, fam_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_family_members(self, user_id):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT u.id, u.username FROM users u JOIN family_links f ON u.id = f.family_id WHERE f.user_id = %s", (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_linked_to_user(self, user_id):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT u.id, u.username FROM users u JOIN family_links f ON u.id = f.user_id WHERE f.family_id = %s", (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def add_data(self, user_id, data_type, title, content, date=None, time=None, voice_note=None,file_data=None,file_name=None):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_data (user_id, data_type, title, content, date, time, voice_note,file_data,file_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s)
            """, (user_id, data_type, title, content, date, time, voice_note,file_data,file_name))
            conn.commit()

            # also share memory with linked family
            family_members = self.get_linked_to_user(user_id)
            for fam in family_members:
                cursor.execute("""
                    INSERT INTO user_data (user_id, data_type, title, content, date, time, voice_note,file_data,file_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s)
                """, (fam['id'], data_type, title + " (Shared from family)", content, date, time, voice_note,file_data,file_name))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_user_data(self, user_id, data_type=None):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            if data_type:
                cursor.execute("SELECT * FROM user_data WHERE user_id = %s AND data_type = %s ORDER BY id DESC", (user_id, data_type))
            else:
                cursor.execute("SELECT * FROM user_data WHERE user_id = %s ORDER BY id DESC", (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def memory_exists(self, user_id, data_type, title, content, date, time):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM user_data 
                WHERE user_id = %s AND data_type = %s AND title = %s AND content = %s 
                AND date = %s AND time = %s
            """, (user_id, data_type, title, content, date, time))
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    def delete_all_user_data(self, user_id):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_data WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def delete_memory(self, memory_id):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_data WHERE id = %s", (memory_id,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def get_all_memories_for_user(self, user_id):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_data WHERE user_id = %s ORDER BY id DESC", (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()
