import streamlit as st
import bcrypt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from database import Database

# Load .env if you ever want to store secrets there
load_dotenv()

# Streamlit config
st.set_page_config(page_title="🧠 Personal Memory Assistant", layout="wide")

# Connect to DB
db = Database()
conn = db.connect()
print("🧪 Connection object:", conn)

if not conn:
    st.error("🚨 Could not connect to MySQL. Check credentials.")
    st.stop()

# Session state
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# Navigation
def set_page(name): st.session_state['page'] = name

def authenticate(username, password):
    user = db.get_user(username)
    if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        st.session_state['user_id'] = user['id']
        st.session_state['username'] = user['username']
        set_page('home')
        return True
    return False

def logout():
    st.session_state['user_id'] = None
    st.session_state['username'] = None
    set_page('login')

# --- PAGES ---
def login_page():
    st.title("🔐 Welcome to Personal Memory Assistant")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 Login")
        with st.form("login"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if authenticate(uname, pwd):
                    st.success("✅ Logged in")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

    with col2:
        st.subheader("📝 Sign Up")
        with st.form("signup"):
            new_user = st.text_input("New Username")
            new_pwd = st.text_input("New Password", type="password")
            created = st.form_submit_button("Sign Up")
            if created:
                if db.create_user(new_user, new_pwd):
                    st.success("✅ Account created")
                else:
                    st.error("❌ Username exists")

def home_page():
    st.sidebar.success(f"👋 Hi, {st.session_state['username']}")
    if st.sidebar.button("Home"): set_page("home")
    if st.sidebar.button("Add Memory"): set_page("add_memory")
    if st.sidebar.button("Search"): set_page("search_memory")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    if st.session_state['page'] == "home":
        show_dashboard()
    elif st.session_state['page'] == "add_memory":
        add_memory()
    elif st.session_state['page'] == "search_memory":
        search_memory()

def show_dashboard():
    st.title("📊 Dashboard")
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)

    all_data = db.get_user_data(st.session_state['user_id'])

    st.subheader("🔔 Reminders (next 7 days)")
    reminders = [r for r in all_data if r['date'] and today <= r['date'] <= upcoming]
    if reminders:
        for r in reminders:
            st.info(f"📌 **{r['title']}** ({r['data_type']}) on **{r['date']}**")
    else:
        st.info("No reminders")

    st.subheader("🕒 Last Memories")
    for item in all_data[:5]:
        st.markdown(f"**{item['title']}** - {item['data_type']} - {item['date'] or 'No date'}")
        st.caption(item['content'])
        st.markdown("---")

def add_memory():
    st.title("📝 Add Memory")

    with st.form("add"):
        dtype = st.selectbox("Type", ['journal', 'document', 'asset', 'insurance', 'medication', 'address', 'key_date'])
        title = st.text_input("Title")
        content = st.text_area("Content")
        date = st.date_input("Date", value=None) if dtype in [ 'insurance', 'medication'] else None
        saved = st.form_submit_button("Save")

        if saved:
            if title and content:
                db.add_data(st.session_state['user_id'], dtype, title, content, date)
                st.success("✅ Memory added")
            else:
                st.warning("Please fill all fields")

def search_memory():
    st.title("🔍 Search Memories")
    query = st.text_input("Keyword or Date")

    if query:
        results = [
            item for item in db.get_user_data(st.session_state['user_id'])
            if query.lower() in item['title'].lower()
            or query.lower() in item['content'].lower()
            or (item['date'] and query in str(item['date']))
        ]
        if results:
            for r in results:
                st.markdown(f"**{r['title']}** - {r['data_type']} - {r['date'] or 'No date'}")
                st.caption(r['content'])
                st.markdown("---")
        else:
            st.info("No match found.")

# --- App Entry ---
if st.session_state['user_id']:
    home_page()
else:
    login_page()
