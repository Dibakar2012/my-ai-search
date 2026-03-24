import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json
from groq import Groq

# --- ১. Page Setup ---
st.set_page_config(page_title="Dibakar AI", layout="wide")

# --- ২. Bulletproof Firebase Initialization (JSON Method) ---
@st.cache_resource
def init_db():
    if not firebase_admin._apps:
        try:
            # এক লাইনের JSON স্ট্রিং থেকে সরাসরি ডাটা নেবে, কোনো এরর হবে না
            fb_dict = json.loads(st.secrets["FIREBASE_JSON"])
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Config Error: {e}")
            st.stop()
    return firestore.client()

db = init_db()

# --- ৩. Database Functions ---
def get_user(email):
    doc_ref = db.collection("users").document(email)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        data = {"credits": 10, "signup_date": str(datetime.date.today())}
        doc_ref.set(data)
        return data

def update_credits(email, amount):
    db.collection("users").document(email).update({"credits": amount})

# --- ৪. UI & CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #050810; color: white; }
    .main-title { font-size: 3.5rem; font-weight: 800; text-align: center; background: linear-gradient(45deg, #3B82F6, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 10px; }
    .plan-card { background: #111827; padding: 25px; border-radius: 15px; border: 1px solid #374151; text-align: center; }
    .premium-card { border: 2px solid #8B5CF6; background: linear-gradient(135deg, #0F172A, #1E1B4B); }
    .call-btn { background: #22C55E; color: white; padding: 15px; border-radius: 10px; text-decoration: none; display: block; font-weight: bold; text-align: center; font-size: 18px; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ৫. Login System ---
if "user_email" not in st.session_state:
    st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>India's Ultimate AI Search Engine</p>", unsafe_allow_html=True)
    
    email_login = st.text_input("আপনার ইমেইল দিন:", placeholder="example@gmail.com")
    if st.button("লগইন / সাইনআপ", use_container_width=True):
        if email_login:
            st.session_state.user_email = email_login.lower().strip()
            st.rerun()
    st.stop()

# Load Data
email = st.session_state.user_email
user_data = get_user(email)
user_credits = user_data.get('credits', 0)
is_admin = (email == "dibakar61601@gmail.com")

# --- ৬. Sidebar (Profile & Admin) ---
with st.sidebar:
    st.title("👤 প্রোফাইল")
    st.write(f"ইমেইল: **{email}**")
    st.write(f"ক্রেডিট বাকি: **{user_credits if not is_admin else 'Unlimited 💎'}**")
    
    if is_admin:
        st.markdown("---")
        st.subheader("👑 অ্যাডমিন প্যানেল")
        target_email = st.text_input("ইউজার ইমেইল")
        c_amount = st.number_input("ক্রেডিট দিন", min_value=0, value=75)
        if st.button("পেমেন্ট কনফার্ম"):
            update_credits(target_email.lower().strip(), c_amount)
            st.success("ক্রেডিট পাঠানো হয়েছে!")

    if st.button("লগআউট"):
        del st.session_state.user_email
        st.rerun()

# --- ৭. Main Content (Search & AI) ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

if user_credits <= 0 and not is_admin:
    st.error("আপনার ফ্রি সার্চ শেষ! প্লিজ রিচার্জ করুন।")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="plan-card"><h3>Standard</h3><h1>₹99</h1><hr><p>✅ ৩০০ সার্চ</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="plan-card premium-card"><h3>Offer 🚀</h3><h1>₹35</h1><hr><p>✅ ৭৫ সার্চ</p></div>', unsafe_allow_html=True)
    
    st.markdown('<a href="tel:+919242959903" class="call-btn">📞 পেমেন্ট করে কল করুন: 9242959903</a>', unsafe_allow_html=True)

else:
    query = st.chat_input("যেকোনো কিছু জিজ্ঞেস করুন...")
    if query:
        st.chat_message("user").write(query)
        
        with st.spinner("Dibakar AI ভাবছে..."):
            try:
                # Groq API দিয়ে আসল AI উত্তর তৈরি
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": query}],
                    model="llama3-8b-8192", 
                )
                ai_answer = response.choices[0].message.content
                st.chat_message("assistant").write(ai_answer)
                
                # ক্রেডিট কমানো
                if not is_admin:
                    update_credits(email, user_credits - 1)
                    st.rerun()
            except Exception as e:
                st.error("এআই সার্ভারে সমস্যা হচ্ছে। একটু পর আবার চেষ্টা করুন।")
