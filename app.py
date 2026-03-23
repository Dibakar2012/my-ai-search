import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import re

# 1. Secrets Management
try:
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API Keys missing! Please add them in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

# --- UI Setup & Premium CSS ---
st.set_page_config(page_title="Dibakar AI", layout="centered")

st.markdown("""
    <style>
    /* মেইন ব্যাকগ্রাউন্ড ফিক্স */
    .stApp {
        background-color: #070B16;
        color: #E2E8F0;
    }
    
    /* নিচের সাদা বারটি মুছে ফেলার জন্য */
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stBottom"] {
        background-color: transparent !important;
    }
    [data-testid="stChatInput"] {
        background-color: #121827 !important;
        border: 1px solid #2D3748 !important;
        border-radius: 15px !important;
    }

    /* টাইটেল */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ইউজার মেসেজ বাবল */
    .user-msg {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 20px;
        border: 1px solid #334155;
        max-width: 80%;
        margin-left: auto;
    }

    /* এআই মেসেজ বাবল */
    .ai-msg {
        background-color: #111827;
        padding: 20px;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 25px;
        border: 1px solid #1F2937;
        line-height: 1.7;
    }

    /* সোর্স কার্ড */
    .source-tag {
        display: inline-block;
        background: #1F2937;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        color: #60A5FA;
        margin-right: 5px;
        border: 1px solid #374151;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State for Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Logic Functions ---
def clean_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside']): tag.decompose()
        return " ".join(soup.get_text().split())[:1500]
    except: return ""

def get_ai_response(user_input):
    # সার্চ লজিক
    search_res = requests.post("https://google.serper.dev/search", 
                               headers={'X-API-KEY': SERPER_API_KEY}, 
                               json={"q": user_input, "num": 3}).json()
    context = ""
    links = []
    for item in search_res.get('organic', []):
        links.append(item['link'])
        context += f"\nSource: {item['link']}\nContent: {clean_scrape(item['link'])}\n"

    system_msg = "You are Dibakar AI. Use provided context to answer. Be direct and use the user's language."
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system_msg},
                  {"role": "user", "content": f"Context: {context}\nQuestion: {user_input}"}],
        temperature=0.3
    )
    return response.choices[0].message.content, links

# --- UI Display ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# চ্যাট হিস্ট্রি দেখানো
for chat in st.session_state.messages:
    if chat["role"] == "user":
        st.markdown(f'<div class="user-msg">{chat["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-msg">{chat["content"]}</div>', unsafe_allow_html=True)
        if "links" in chat:
            cols = st.columns(len(chat["links"]))
            for i, link in enumerate(chat["links"]):
                st.markdown(f'<a href="{link}" class="source-tag">Source [{i+1}]</a>', unsafe_allow_html=True)

# ইনপুট বক্স (চ্যাট স্টাইল)
if prompt := st.chat_input("Ask about anything..."):
    # ইউজার মেসেজ সেভ করা
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)

    # এআই রেসপন্স
    with st.spinner("Analyzing..."):
        answer, sources = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer, "links": sources})
        st.rerun() # স্ক্রিন রিফ্রেশ করে মেসেজগুলো সাজানোর জন্য
