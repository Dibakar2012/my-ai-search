import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time

# --- ১. Firebase Initialization ---
if not firebase_admin._apps:
    try:
        # নিশ্চিত করো 'serviceAccountKey.json' ফাইলটি তোমার ফোল্ডারে আছে
        cred = credentials.Certificate("serviceAccountKey.json") 
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Key Error: {e}")

db = firestore.client()

# --- ২. Database Functions ---
def get_user_data(email):
    doc_ref = db.collection("users").document(email.lower())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # নতুন ইউজারদের জন্য ১০ ফ্রি ক্রেডিট সেট করা হচ্ছে
        data = {"credits": 10, "signup_date": str(datetime.date.today())}
        doc_ref.set(data)
        return data

def update_db_credits(email, amount):
    db.collection("users").document(email.lower()).update({"credits": amount})

# --- ৩. UI & Styling ---
st.set_page_config(page_title="Dibakar AI", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #070B16; color: white; }
    .main-title { font-size: 3.5rem; font-weight: 800; text-align: center; background: linear-gradient(to right, #60A5FA, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
    .plan-box { background: #111827; padding: 25px; border-radius: 15px; border: 1px solid #1E293B; text-align: center; margin-bottom: 20px; }
    .premium-box { background: linear-gradient(135deg, #1E1B4B, #4C1D95); border: 2px solid #A78BFA; }
    .call-btn { width: 100%; background: #25D366; color: white; padding: 18px; border-radius: 12px; text-align: center; font-size: 20px; font-weight: bold; text-decoration: none; display: block; margin-top: 10px; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- ৪. Session & Login ---
if "user_email" not in st.session_state:
    st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)
    st.subheader("Login to start searching")
    email_input = st.text_input("আপনার ইমেইল আইডি দিন")
    if st.button("লগইন / সাইনআপ"):
        if email_input:
            st.session_state.user_email = email_input.lower()
            st.rerun()
    st.stop()

# Load User Data from Firebase
user_data = get_user_data(st.session_state.user_email)
current_credits = user_data['credits']
is_admin = st.session_state.user_email == "dibakar61601@gmail.com"

# --- ৫. Sidebar (Profile & Admin) ---
with st.sidebar:
    st.title("Dibakar AI Dashboard")
    st.write(f"📧 ইউজার: {st.session_state.user_email}")
    st.write(f"⭐ ক্রেডিট: {current_credits if not is_admin else 'Unlimited 💎'}")
    
    if is_admin:
        st.markdown("---")
        if st.checkbox("👑 Admin Dashboard (ম্যানুয়াল অ্যাপ্রুভাল)"):
            target = st.text_input("ক্রেডিট দিতে ইউজারের ইমেইল লিখুন")
            if st.button("Approve ₹35 (75 Credits)"):
                update_db_credits(target, 75)
                st.success(f"75 Credits added to {target}")
            if st.button("Approve ₹99 (300 Credits)"):
                update_db_credits(target, 300)
                st.success(f"300 Credits added to {target}")
    
    if st.button("লগআউট"):
        del st.session_state.user_email
        st.rerun()

# --- ৬. Main App Logic ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# ক্রেডিট চেক
if current_credits <= 0 and not is_admin:
    st.error("আপনার ফ্রি ক্রেডিট শেষ হয়ে গেছে! সার্চ চালিয়ে যেতে রিচার্জ করুন।")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="plan-box">
                <h3 style="color:#94A3B8;">Standard Plan</h3>
                <h1>₹99</h1>
                <p>✅ ৩০০টি এআই রিকোয়েস্ট</p>
                <p>✅ হাই স্পিড সার্ভার অ্যাক্সেস</p>
                <p>✅ কোনো ডেইলি লিমিট নেই</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="plan-box premium-box">
                <h3 style="color:#A78BFA;">Special Offer 🚀</h3>
                <h1>₹35</h1>
                <p>✅ ৭৫টি এআই রিকোয়েস্ট</p>
                <p>✅ ফুল প্রিমিয়াম ফিচার</p>
                <p>✅ স্টুডেন্টদের জন্য সেরা অফার</p>
            </div>
        """, unsafe_allow_html=True)
    
    # তোমার দেওয়া ফোন নাম্বারে কল বাটন
    st.markdown('<a href="tel:+919242959903" class="call-btn">📞 পেমেন্ট করে আমাকে কল করুন (Approval)</a>', unsafe_allow_html=True)
    st.info("পেমেন্ট করার পর উপরের বাটনে ক্লিক করে আমাকে (দিবাকর) কল করুন।")

else:
    # সার্চ বার
    query = st.chat_input("এআই কে কিছু জিজ্ঞেস করুন (যেমন: আজকের খবর কী?)...")
    if query:
        st.chat_message("user").write(query)
        with st.spinner("AI ভাবছে..."):
            # এখানে তোমার আসল সার্চ এপিআই (Groq/Serper) কল হবে
            time.sleep(2) 
            st.chat_message("assistant").write(f"আমি আপনার প্রশ্নের উত্তর তৈরি করছি... (এখানে উত্তর দেখা যাবে)")
            
            # ক্রেডিট কমানো (অ্যাডমিন বাদে)
            if not is_admin:
                update_db_credits(st.session_state.user_email, current_credits - 1)
                st.rerun()
