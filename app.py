import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time

# --- ১. Firebase Initialization ---
# নিশ্চিত করো 'serviceAccountKey.json' ফাইলটি একই ফোল্ডারে আছে
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json") 
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("Firebase চাবি (JSON ফাইল) খুঁজে পাওয়া যায়নি। দয়া করে ফাইলটি ফোল্ডারে রাখুন।")

db = firestore.client()

# --- ২. Database Functions ---
def get_user_data(email):
    doc_ref = db.collection("users").document(email.lower())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # নতুন ইউজারদের জন্য ১০ ফ্রি ক্রেডিট এবং আজকের তারিখ সেভ করা
        data = {
            "credits": 10, 
            "signup_date": str(datetime.date.today()),
            "status": "Free"
        }
        doc_ref.set(data)
        return data

def update_db_credits(email, amount):
    db.collection("users").document(email.lower()).update({"credits": amount})

# --- ৩. UI Styling (Premium Dark Theme) ---
st.set_page_config(page_title="Dibakar AI", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #070B16; color: white; }
    .main-title { font-size: 3.5rem; font-weight: 800; text-align: center; background: linear-gradient(to right, #60A5FA, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
    .plan-box { background: #111827; padding: 25px; border-radius: 15px; border: 1px solid #1E293B; text-align: center; height: 100%; transition: 0.3s; }
    .premium-box { background: linear-gradient(135deg, #1E1B4B, #4C1D95); border: 2px solid #A78BFA; box-shadow: 0 10px 30px rgba(167, 139, 250, 0.2); }
    .call-btn { width: 100%; background: #25D366; color: white; padding: 18px; border-radius: 12px; text-align: center; font-size: 20px; font-weight: bold; text-decoration: none; display: block; margin-top: 20px; box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4); }
    .call-btn:hover { background: #1eb954; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- ৪. Login / Session Management ---
if "user_email" not in st.session_state:
    st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>India's Most Powerful AI Search Engine</p>", unsafe_allow_html=True)
    
    with st.container():
        email_input = st.text_input("Enter your email to start", placeholder="example@gmail.com")
        if st.button("Login / Create Account", use_container_width=True):
            if email_input:
                st.session_state.user_email = email_input.lower()
                st.rerun()
    st.stop()

# Load Data
user_data = get_user_data(st.session_state.user_email)
current_credits = user_data['credits']
# তোমার স্পেশাল ইমেল চেক
is_admin = st.session_state.user_email == "dibakar61601@gmail.com"

# --- ৫. Sidebar (Admin & History) ---
with st.sidebar:
    st.title("Settings")
    st.write(f"Logged in: **{st.session_state.user_email}**")
    st.write(f"Credits: **{current_credits if not is_admin else 'Unlimited 💎'}**")
    
    if is_admin:
        st.markdown("---")
        st.subheader("👑 Admin Panel")
        target_mail = st.text_input("User Email")
        if st.button("Approve ₹35 (75 Credits)"):
            update_db_credits(target_mail, 75)
            st.success("75 Credits Added!")
        if st.button("Approve ₹99 (300 Credits)"):
            update_db_credits(target_mail, 300)
            st.success("300 Credits Added!")
            
    if st.button("Logout"):
        del st.session_state.user_email
        st.rerun()

# --- ৬. Main Content ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# ক্রেডিট শেষ হলে রিচার্জ অপশন
if current_credits <= 0 and not is_admin:
    st.error("আপনার ফ্রি ক্রেডিট শেষ হয়ে গেছে! সার্চ চালিয়ে যেতে প্ল্যান বেছে নিন।")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="plan-box">
                <h3 style="color:#94A3B8;">Standard Plan</h3>
                <h1>₹99</h1>
                <p>✅ 300 AI Search Requests</p>
                <p>✅ Super Fast Response</p>
                <p>✅ No Daily Limit</p>
                <p>✅ Access All Features</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="plan-box premium-box">
                <h3 style="color:#A78BFA;">Special Offer 🚀</h3>
                <h1>₹35</h1>
                <p>✅ 75 AI Search Requests</p>
                <p>✅ Student Friendly Price</p>
                <p>✅ All Pro Models Included</p>
                <p>✅ Priority Support</p>
            </div>
        """, unsafe_allow_html=True)

    # কল বাটন
    st.markdown('<a href="tel:+919242959903" class="call-btn">📞 পেমেন্ট করে আমাকে কল করুন (Approval)</a>', unsafe_allow_html=True)
    st.info("নোট: পেমেন্ট করার পর উপরের বাটনে ক্লিক করে সরাসরি আমার সাথে কথা বলুন।")

else:
    # সার্চ বার
    query = st.chat_input("Ask Dibakar AI anything...")
    if query:
        st.chat_message("user").write(query)
        with st.spinner("AI is thinking..."):
            # এখানে তোমার আসল AI API বসবে
            time.sleep(2) 
            st.chat_message("assistant").write(f"Here is the answer for: {query}")
            
            # ক্রেডিট আপডেট (অ্যাডমিন বাদে)
            if not is_admin:
                new_val = current_credits - 1
                update_db_credits(st.session_state.user_email, new_val)
                st.rerun()
