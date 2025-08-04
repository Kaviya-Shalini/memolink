
import openai
import streamlit as st
import bcrypt
from datetime import datetime, timedelta, time as dtime
import os
from openai import OpenAI
from dotenv import load_dotenv
from database import Database
import base64
import streamlit.components.v1 as components

# Load environment variables (optional)
client = openai.OpenAI(
    api_key="b50F06IeU8hnwtnI513qEhNO6QGug9KVcOJ4vUbsNCI",  # replace with your actual Poe key
    base_url="https://api.poe.com/v1",
)
st.set_page_config(page_title="🧐 Personal Memory Assistant", layout="wide")

db = Database()
conn = db.connect()
if not conn:
    st.error("🚨 Could not connect to MySQL. Check credentials.")
    st.stop()

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'reminder_shown' not in st.session_state:
    st.session_state['reminder_shown'] = set()
if 'memory_type' not in st.session_state:
    st.session_state['memory_type'] = None


def set_page(name):
    st.session_state['page'] = name

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
    if st.sidebar.button("🏠 Home"): set_page("home")
    if st.sidebar.button("🧠 Add Memory"): set_page("add_memory")
    if st.sidebar.button("🔎 Search"): set_page("search_memory")
    if st.sidebar.button("👪 Add Family Member"): set_page("add_family")
    if st.sidebar.button("chatBot assistant"): set_page("chat_with_bot")
    if st.sidebar.button("🗑️ Clear All Memories"):
        if db.delete_all_user_data(st.session_state['user_id']):
            st.sidebar.success("✅ All memories deleted")
        else:
            st.sidebar.error("❌ Failed to delete memories")
    if st.sidebar.button("🚪 Logout"):
        logout()
        st.rerun()

    if st.session_state['page'] == "home":
        show_dashboard()
    elif st.session_state['page'] == "add_memory":
        add_memory()
    elif st.session_state['page'] == "search_memory":
        search_memory()
    elif st.session_state['page'] == "add_family":
        add_family()
    elif st.session_state['page'] == "chat_with_bot":
        chat_with_bot()
        

def chat_with_bot():
    st.subheader("🤖 Poe AI Chat Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_prompt = st.chat_input("Ask anything...")

    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})

        with st.chat_message("user"):
            st.markdown(user_prompt)

        try:
            response = client.chat.completions.create(
                model="API-Integrator",  # Ensure this is your valid Poe model
                messages=st.session_state.chat_history,
            )

            bot_reply = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

            with st.chat_message("assistant"):
                st.markdown(bot_reply)

        except Exception as e:
            st.error(f"❌ Error: {e}")

           
# Then call this function somewhere in your Streamlit app
# like inside your home page
if st.session_state.get("logged_in"):
    chat_with_bot()

def add_family():
    st.title("👪 Add Family Member")
    fam_username = st.text_input("Enter existing username of your family member")
    if st.button("Add Family Member"):
        if db.link_family_member(st.session_state['user_id'], fam_username):
            st.success(f"✅ Linked to {fam_username} successfully")
        else:
            st.warning(f"⚠️ Could not link to {fam_username}. Maybe already linked or user does not exist.")

    linked_users = db.get_linked_to_user(st.session_state['user_id'])
    if linked_users:
        st.subheader("🔗 Linked By")
        for user in linked_users:
            st.markdown(f"- {user['username']}")

def show_dashboard():
    st.title("📊 Dashboard")
    now = datetime.now()
    all_data = db.get_user_data(st.session_state['user_id'])

    st.subheader("🔔 Reminders")
    for r in all_data:
        if r['date'] and r.get('time'):
            reminder_dt = datetime.combine(r['date'], datetime.strptime(r['time'], "%H:%M").time())
            time_diff = (now - reminder_dt).total_seconds()
            if 0 <= time_diff <= 60 and r['id'] not in st.session_state['reminder_shown']:
                st.warning(f"🔔 Alert: {r['title']} - {r['data_type']} - Due now!")
                st.session_state['reminder_shown'].add(r['id'])
                st.toast(f"🔔 WhatsApp-style Reminder: {r['title']} is due now!", icon="🔔")
                components.html(f"""
                <script>
                    var msg = new SpeechSynthesisUtterance("Reminder alert: {r['title']} is due now.");
                    window.speechSynthesis.speak(msg);
                </script>
                """, height=0)

    st.subheader("🕒 Recent Memories")
    for item in all_data[:5]:
        st.markdown(f"**{item['title']}** - {item['data_type']} - {item['date'] or 'No date'}")
        st.caption(item['content'])
        if item.get('voice_note'):
            st.audio(base64.b64decode(item['voice_note']), format='audio/wav')
        if item.get('file_data'):
            st.download_button("📥 Download File", data=base64.b64decode(item['file_data']), file_name=item['file_name'])
        st.markdown("---")

def add_memory():
    st.title("📝 Add Memory")

    st.subheader("Select Type")
    cols = st.columns(4)
    types = ['othernote', 'document', 'asset', 'insurance', 'medication', 'address', 'key_date']
    for i, t in enumerate(types):
        if cols[i % 4].button(t.capitalize()):
            st.session_state['memory_type'] = t

    dtype = st.session_state.get('memory_type')
    if not dtype:
        st.info("Select a type to proceed.")
        return

    with st.form("add", clear_on_submit=True):
        title = st.text_input("Title")
        content = st.text_area("Content")
        date = st.date_input("Reminder Date", value=None)
        time = st.time_input("Reminder Time", value=dtime(9, 0))
        file = st.file_uploader("Upload file (optional)", type=None)
        voice_note = st.file_uploader("Upload voice note (optional)", type=["mp3", "wav"])

        extra_info = ""
        valid = True

        if dtype == 'insurance':
            col1, col2 = st.columns(2)
            with col1:
                monthly_due = st.date_input("Monthly Due Date")
            with col2:
                maturity = st.date_input("Maturity Date")
            extra_info += f"\nMonthly Due: {monthly_due}, Maturity: {maturity}"

        elif dtype == 'medication':
            col1, col2 = st.columns(2)
            with col1:
                med_name = st.text_input("Medication Name")
            with col2:
                dosage = st.text_input("Dosage")
            extra_info += f"\nMedication: {med_name}, Dosage: {dosage}"

        saved = st.form_submit_button("💾 Save")
        if saved:
            if title and content and valid:
                final_content = content + extra_info
                voice_data = base64.b64encode(voice_note.read()).decode() if voice_note else None
                file_data = base64.b64encode(file.read()).decode() if file else None
                file_name = file.name if file else None

                if not db.memory_exists(st.session_state['user_id'], dtype, title, final_content, date, time.strftime("%H:%M")):
                    db.add_data(st.session_state['user_id'], dtype, title, final_content, date, time.strftime("%H:%M"), voice_data, file_data, file_name)
                    st.success("✅ Memory added with reminder")
                    st.toast("⏰ Reminder has been set", icon="⏰")
                else:
                    st.warning("⚠️ Duplicate memory detected")
            else:
                st.warning("Please fill all required fields.")

def search_memory():
    st.title("🔍 Search & Manage Memories")
    query = st.text_input("Search by keyword or date")
    all_data = db.get_user_data(st.session_state['user_id'])

    results = [
        r for r in all_data
        if query.lower() in r['title'].lower() or query.lower() in r['content'].lower()
        or (r['date'] and query in str(r['date']))
    ] if query else all_data

    if results:
        for r in results:
            st.markdown(f"**{r['title']}** - {r['data_type']} - {r['date'] or 'No date'}")
            st.caption(r['content'])
            if r.get('voice_note'):
                st.audio(base64.b64decode(r['voice_note']), format='audio/wav')
            if r.get('file_data'):
                st.download_button("📥 Download File", data=base64.b64decode(r['file_data']), file_name=r['file_name'])
            if st.button(f"❌ Delete {r['title']}", key=f"del_{r['id']}"):
                db.delete_memory(r['id'])
                st.success("✅ Deleted")
                st.rerun()
            st.markdown("---")
    else:
        st.info("🔍 No matching memories found.")

if st.session_state['user_id']:
    home_page()
else:
    login_page()
