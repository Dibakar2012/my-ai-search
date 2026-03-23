import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from urllib.parse import urlparse
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
    /* মেইন ব্যাকগ্রাউন্ড */
    .stApp {
        background-color: #070B16 !important;
        color: #E2E8F0;
    }
    
    /* নিচের সাদা অংশ ফিক্স */
    div[data-testid="stBottom"] {
        background-color: transparent !important;
    }

    /* টাইটেল */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* টেক্সট বক্স ডিজাইন (বোল্ড টেক্সট সহ) */
    [data-testid="stChatInput"] {
        background-color: #121827 !important;
        border: 2px solid #3B82F6 !important; /* Blue border */
        border-radius: 15px !important;
    }
    
    /* ইনপুট টেক্সট বোল্ড করা */
    [data-testid="stChatInput"] textarea {
        font-weight: 700 !important; /* Bold Text */
        color: #FFFFFF !important;
        font-size: 17px !important;
    }

    /* ইউজার মেসেজ বাবল */
    .user-msg {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 20px;
        border: 1px solid #334155;
        max-width: 85%;
        margin-left: auto;
        font-weight: 500;
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
    .source-container {
        display: flex;
        flex-wrap: wrap;
        margin-top: 10px;
    }
    .source-tag {
        display: flex;
        align-items: center;
        background: #1F2937;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #60A5FA;
        margin-right: 10px;
        margin-bottom: 10px;
        border: 1px solid #374151;
        text-decoration: none;
    }
    .source-tag img {
        width: 16px;
        height: 16px;
        margin-right: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Logic Functions ---
def get_domain_logo(url):
    domain = urlparse(url).netloc
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32", domain

def get_ai_response(user_input):
    # Greeting detection
    greetings = ["hi", "hii", "hello", "kaise ho", "kemon acho", "hlo"]
    user_lower = user_input.lower().strip()
    is_greeting = user_lower in greetings or len(user_lower.split()) < 3
    
    context = ""
    links = []

    if not is_greeting:
        try:
            search_res = requests.post("https://google.serper.dev/search", 
                                       headers={'X-API-KEY': SERPER_API_KEY}, 
                                       json={"q": user_input, "num": 3}).json()
            for item in search_res.get('organic', []):
                links.append(item['link'])
                context += f"Source: {item['link']}\nSnippet: {item.get('snippet','')}\n"
        except: pass

    # Strict language system prompt
    system_instruction = """
    You are Dibakar AI. 
    CRITICAL RULE: Always respond in the EXACT language used by the user.
    - User says 'Hii' or 'Hello' -> Respond in English (e.g., 'Hii! I am fine. How can I help you?').
    - User says 'Kaise ho' -> Respond in Hindi (e.g., 'Main theek hoon, aap kaise hain?').
    - User says 'Kemon acho' -> Respond in Bengali (e.g., 'Ami bhalo achi, tumi kemon acho?').
    DO NOT explain word meanings. DO NOT mention defense companies for greetings.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system_instruction},
                  {"role": "user", "content": f"Context: {context}\nQuestion: {user_input}"}],
        temperature=0.1
    )
    return response.choices[0].message.content, links

# --- Dibakar AI UI ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

for chat in st.session_state.messages:
    if chat["role"] == "user":
        st.markdown(f'<div class="user-msg">{chat["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-msg">{chat["content"]}</div>', unsafe_allow_html=True)
        if "links" in chat and chat["links"]:
            st.markdown('<div class="source-container">', unsafe_allow_html=True)
            for i, link in enumerate(chat["links"]):
                logo_url, domain = get_domain_logo(link)
                st.markdown(f'<a href="{link}" target="_blank" class="source-tag"><img src="{logo_url}"> {domain}</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Processing..."):
        answer, sources = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer, "links": sources})
    st.rerun()
