import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- Firebase Initialization ---
if not firebase_admin._apps:
    try:
        # এটি তোমার দেওয়া Secrets থেকে তথ্য পড়বে
        if "firebase" in st.secrets:
            firebase_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_dict)
            firebase_admin.initialize_app(cred)
        else:
            st.error("Secrets-এ 'firebase' ডাটা পাওয়া যায়নি!")
    except Exception as e:
        st.error(f"Error: {e}")

db = firestore.client()
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time

# --- 1. Firebase Initialization (Using Secrets) ---
if not firebase_admin._apps:
    try:
        # Streamlit Secrets se credentials uthayega
        firebase_secrets = dict(st.secrets["firebase"])
        cred = credentials.Certificate(firebase_secrets)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("Firebase setup missing! Please add credentials in Streamlit Secrets.")

db = firestore.client()

# --- 2. Database Functions ---
def get_user_data(email):
    doc_ref = db.collection("users").document(email.lower())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # Naye user ko 10 free credits milenge
        data = {"credits": 10, "signup_date": str(datetime.date.today())}
        doc_ref.set(data)
        return data

def update_db_credits(email, amount):
    db.collection("users").document(email.lower()).update({"credits": amount})

# --- 3. Page Config & Styling ---
st.set_page_config(page_title="Dibakar AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050810; color: white; }
    .main-title { font-size: 3rem; font-weight: 800; text-align: center; background: linear-gradient(45deg, #3B82F6, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 20px; }
    .plan-card { background: #111827; padding: 20px; border-radius: 15px; border: 1px solid #374151; text-align: center; }
    .call-btn { background: #22C55E; color: white; padding: 12px; border-radius: 8px; text-decoration: none; display: block; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. Login System ---
if "user_email" not in st.session_state:
    st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)
    email_login = st.text_input("Apna Gmail enter karein:", placeholder="example@gmail.com")
    if st.button("Start Searching"):
        if email_login:
            st.session_state.user_email = email_login.lower()
            st.rerun()
    st.stop()

# Load User Data
user_info = get_user_data(st.session_state.user_email)
user_credits = user_info['credits']
is_admin = st.session_state.user_email == "dibakar61601@gmail.com"

# --- 5. Navigation (3 Dots / Sidebar) ---
with st.sidebar:
    st.title("Settings")
    st.write(f"User: {st.session_state.user_email}")
    st.write(f"Credits Left: **{user_credits if not is_admin else 'Unlimited 💎'}**")
    
    if is_admin:
        st.markdown("---")
        st.subheader("👑 Admin Dashboard")
        target_user = st.text_input("User ka email daalein:")
        new_credit_amount = st.number_input("Kitne credits dena hai?", min_value=0, value=75)
        if st.button("Approve Payment"):
            update_db_credits(target_user, new_credit_amount)
            st.success(f"{target_user} ko credits mil gaye!")

    if st.button("Logout"):
        del st.session_state.user_email
        st.rerun()

# --- 6. Main Interface ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

if user_credits <= 0 and not is_admin:
    st.warning("Aapke 10 free search khatam ho gaye hain!")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="plan-card"><h3>Plan ₹35</h3><p>75 AI Searches</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="plan-card"><h3>Plan ₹99</h3><p>300 AI Searches</p></div>', unsafe_allow_html=True)
    
    st.markdown(f'<a href="tel:+919242959903" class="call-btn">📞 Recharge ke liye Dibakar ko Call karein: 9242959903</a>', unsafe_allow_html=True)

else:
    user_query = st.chat_input("Ask Dibakar AI anything...")
    if user_query:
        st.chat_message("user").write(user_query)
        with st.spinner("Processing..."):
            time.sleep(2) # AI Response delay
            st.chat_message("assistant").write(f"Ye raha aapka jawab: {user_query} ke baare mein...")
            
            if not is_admin:
                update_db_credits(st.session_state.user_email, user_credits - 1)
                st.rerun()
