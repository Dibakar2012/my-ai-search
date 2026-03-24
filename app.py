import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time

# --- ১. Firebase Initialization (Using Secrets) ---
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            fb_dict = dict(st.secrets["firebase"])
            
            # Private Key ফরম্যাট ঠিক করার জাদুকরী লাইন
            if "private_key" in fb_dict:
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        else:
            st.error("Streamlit Secrets-এ 'firebase' সেকশন পাওয়া যায়নি!")
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

# ডেটাবেস কানেক্ট
try:
    db = firestore.client()
except Exception as e:
    st.error(f"Firestore Client Error: {e}")

# --- ২. Database Functions ---
def get_user_data(email):
    doc_ref = db.collection("users").document(email.lower())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # নতুন ইউজারকে ১০ ফ্রি ক্রেডিট দেওয়া হচ্ছে
        data = {"credits": 10, "signup_date": str(datetime.date.today())}
        doc_ref.set(data)
        return data

def update_db_credits(email, amount):
    db.collection("users").document(email.lower()).update({"credits": amount})

# --- ৩. UI Styling ---
st.set_page_config(page_title="Dibakar AI", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #050810; color: white; }
    .main-title { font-size: 3.5rem; font-weight: 800; text-align: center; background: linear-gradient(45deg, #3B82F6, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 20px; }
    .plan-card { background: #111827; padding: 25px; border-radius: 15px; border: 1px solid #374151; text-align: center; }
    .premium-card { border: 2px solid #8B5CF6; background: linear-gradient(135deg, #0F172A, #1E1B4B); }
    .call-btn { background: #22C55E; color: white; padding: 15px; border-radius: 10px; text-decoration: none; display: block; font-weight: bold; text-align: center; font-size: 20px; margin-top: 20px; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- ৪. Login System ---
if "user_email" not in st.session_state:
    st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>India's Future Search Engine</p>", unsafe_allow_html=True)
    
    email_login = st.text_input("আপনার ইমেইল দিন:", placeholder="example@gmail.com")
    if st.button("লগইন / সাইনআপ", use_container_width=True):
        if email_login:
            st.session_state.user_email = email_login.lower()
            st.rerun()
    st.stop()

# Load User Data
user_info = get_user_data(st.session_state.user_email)
user_credits = user_info.get('credits', 0)
is_admin = st.session_state.user_email == "dibakar61601@gmail.com"

# --- ৫. Sidebar (Admin & Profile) ---
with st.sidebar:
    st.title("👤 প্রোফাইল")
    st.write(f"ইমেইল: **{st.session_state.user_email}**")
    st.write(f"ক্রেডিট বাকি: **{user_credits if not is_admin else 'Unlimited 💎'}**")
    
    if is_admin:
        st.markdown("---")
        st.subheader("👑 অ্যাডমিন কন্ট্রোল")
        target_user = st.text_input("ইউজার ইমেইল")
        credit_to_give = st.number_input("ক্রেডিট পরিমাণ", min_value=0, value=75)
        if st.button("পেমেন্ট কনফার্ম করুন"):
            update_db_credits(target_user, credit_to_give)
            st.success(f"{target_user} এর ক্রেডিট আপডেট হয়েছে!")

    if st.button("লগআউট"):
        del st.session_state.user_email
        st.rerun()

# --- ৬. Main Content ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

if user_credits <= 0 and not is_admin:
    st.error("আপনার ফ্রি সার্চ শেষ হয়ে গেছে! অনুগ্রহ করে রিচার্জ করুন।")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="plan-card"><h3>Standard Plan</h3><h1>₹99</h1><hr><p>✅ ৩০০টি সার্চ রিকোয়েস্ট</p><p>✅ প্রো এআই মডেল</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="plan-card premium-card"><h3>Student Offer 🚀</h3><h1>₹35</h1><hr><p>✅ ৭৫টি সার্চ রিকোয়েস্ট</p><p>✅ হাই স্পিড অ্যাক্সেস</p></div>', unsafe_allow_html=True)
    
    # কল বাটন (তোমার নাম্বার দেওয়া আছে)
    st.markdown(f'<a href="tel:+919242959903" class="call-btn">📞 পেমেন্ট করে কল করুন: 9242959903</a>', unsafe_allow_html=True)
    st.info("পেমেন্ট করার পর উপরের বাটনে ক্লিক করে সরাসরি দিবাকরকে কল দিন।")

else:
    # সার্চ বার
    user_query = st.chat_input("যেকোনো কিছু জিজ্ঞেস করুন...")
    if user_query:
        st.chat_message("user").write(user_query)
        with st.spinner("এআই উত্তর তৈরি করছে..."):
            # এখানে তোমার আসল সার্চ লজিক বসবে
            time.sleep(2) 
            st.chat_message("assistant").write(f"আপনার প্রশ্ন: '{user_query}' এর উত্তর এখানে আসবে।")
            
            if not is_admin:
                update_db_credits(st.session_state.user_email, user_credits - 1)
                st.rerun()
