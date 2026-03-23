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

# --- UI Setup & Ultra Premium CSS ---
st.set_page_config(page_title="Dibakar AI", layout="centered")

st.markdown("""
    <style>
    /* মেইন ব্যাকগ্রাউন্ড */
    .stApp {
        background-color: #070B16 !important;
        color: #E2E8F0;
    }
    
    /* নিচের সাদা বারটি মুছে ফেলে পার্পল/ডার্ক ব্লু করার ম্যাজিক */
    [data-testid="stBottom"] {
        background: linear-gradient(to top, #1E1B4B, #070B16) !important;
        border-top: 1px solid #4C1D95 !important;
    }
    [data-testid="stBottom"] > div {
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
        filter: drop-shadow(0 0 10px rgba(167, 139, 250, 0.3));
    }

    /* চ্যাট ইনপুট বক্স - পার্পল গ্লো (Purple Glow) */
    [data-testid="stChatInput"] {
        background-color: #121827 !important;
        border: 2px solid #6366F1 !important; /* Indigo/Purple Border */
        border-radius: 15px !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* ইনপুট টেক্সট বোল্ড */
    [data-testid="stChatInput"] textarea {
        font-weight: 700 !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
    }

    /* মেসেজ বাবল ডিজাইন */
    .user-msg {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 20px;
        border: 1px solid #334155;
        max-width: 85%;
        margin-left: auto;
    }

    .ai-msg {
        background-color: #111827;
        padding: 20px;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 25px;
        border: 1px solid #4C1D95; /* Purple Border */
        line-height: 1.7;
    }

    /* সোর্স ট্যাগ */
    .source-tag {
        display: flex;
        align-items: center;
        background: #1E1B4B;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #A78BFA;
        margin-right: 10px;
        margin-bottom: 10px;
        border: 1px solid #4C1D95;
        text-decoration: none;
    }
    
    /* মেকআপ: অপ্রয়োজনীয় এলিমেন্ট হাইড করা */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- লজিক ফাংশন ---
def get_domain_logo(url):
    domain = urlparse(url).netloc
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=32", domain

def get_ai_response(user_input):
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

    system_instruction = """
    You are Dibakar AI. 
    Always respond in the EXACT language used by the user. 
    If they say 'Hii' respond in English. If 'Kaise ho' respond in Hindi.
    Your UI is purple-themed and premium. Keep answers smart and direct.
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

# চ্যাট হিস্ট্রি রেন্ডার
for chat in st.session_state.messages:
    if chat["role"] == "user":
        st.markdown(f'<div class="user-msg">{chat["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-msg">{chat["content"]}</div>', unsafe_allow_html=True)
        if "links" in chat and chat["links"]:
            cols = st.container()
            with cols:
                html_links = '<div style="display: flex; flex-wrap: wrap;">'
                for i, link in enumerate(chat["links"]):
                    logo_url, domain = get_domain_logo(link)
                    html_links += f'<a href="{link}" target="_blank" class="source-tag"><img src="{logo_url}" style="width:16px; margin-right:8px;"> {domain}</a>'
                html_links += '</div>'
                st.markdown(html_links, unsafe_allow_html=True)

# ইনপুট বক্স
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Analyzing..."):
        answer, sources = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer, "links": sources})
    st.rerun()
