import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
from urllib.parse import urlparse # ডোমেইন নাম বের করার জন্য
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
    /* ১. নিচের সাদা অংশটি গাঢ় ব্লু করার জন্য মেইন ব্যাকগ্রাউন্ড ফিক্স */
    .stApp {
        background-color: #070B16 !important;
        color: #E2E8F0;
    }
    
    /* নিচের সাদা অংশটিকে ফিক্স করা (মোস্ট ইম্পর্টেন্ট) */
    div[data-testid="stBottom"] {
        background-color: transparent !important;
        bottom: 0px !important;
        z-index: 1000 !important;
    }
    div[data-testid="stBottom"] > div {
        background-color: transparent !important;
    }
    
    /* চ্যাট ইনপুট ডার্ক এবং ব্লু গ্লো */
    [data-testid="stChatInput"] {
        background-color: #121827 !important;
        border: 2px solid #2D3748 !important;
        border-radius: 15px !important;
        transition: 0.3s;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #60A5FA !important;
        box-shadow: 0 0 15px rgba(96, 165, 250, 0.3) !important;
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

    /* ইউজার মেসেজ বাবল (Hinglish/Bengali-English Style) */
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

    /* সোর্স কার্ড উইথ লোগো (Modern Style) */
    .source-container {
        display: flex;
        flex-wrap: wrap;
        margin-top: 10px;
    }
    .source-tag {
        display: flex;
        align-items: center;
        background: #1F2937;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 13px;
        color: #60A5FA;
        margin-right: 10px;
        margin-bottom: 10px;
        border: 1px solid #374151;
        text-decoration: none;
        transition: 0.2s;
    }
    .source-tag:hover {
        background: #2D3748;
        border-color: #60A5FA;
    }
    .source-tag img {
        width: 16px;
        height: 16px;
        margin-right: 8px;
        border-radius: 3px;
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

def get_domain_logo(url):
    # ডোমেইন নাম এবং লোগো ফাইলে লিঙ্ক বের করার জন্য
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # Google's S2 converter is used to get the favicon of any website
    logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
    return logo_url, domain

def get_ai_response(user_input):
    # ---Greeting Logic ---
    greetings = ["hi", "hii", "hello", "kaise ho", "kemon acho"]
    user_lower = user_input.lower().strip()
    is_greeting = user_lower in greetings or len(user_lower.split()) < 3
    
    context = ""
    links = []

    if not is_greeting:
        search_res = requests.post("https://google.serper.dev/search", 
                                   headers={'X-API-KEY': SERPER_API_KEY}, 
                                   json={"q": user_input, "num": 3}).json()
        
        for item in search_res.get('organic', []):
            links.append(item['link'])
            context += f"\nSource: {item['link']}\nContent: {clean_scrape(item['link'])}\n"

    # --- Strict System Prompt ---
    system_instruction = f"""
    You are Dibakar AI, a smart research engine. Respond ONLY in the user's language.
    STRICT RULES:
    1. GREETINGS: If user says 'Hi' or 'Hii' or 'Hlo', DO NOT talk about Huntington Ingalls Industries. Just say: "Hii! Main theek hoon, aap kaise ho?" or "Hii! আমি ভালো আছি, তুমি কেমন আছো?"
    2. LANGUAGE MATCH: If user asks in Hinglish, answer in Hinglish. If in Bengali, answer in Bengali.
    3. REPETITION: Do not repeat numbers like '0 · 0 · 0' or technical errors in context.
    4. ACCURACY: Combine internal knowledge with web context. Prioritize accuracy.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system_instruction},
                  {"role": "user", "content": f"Web Context: {context}\n\nQuestion: {user_input}"}],
        temperature=0.1 # কমিয়ে দেওয়া হয়েছে ভুল এড়াতে (Lowest creativity)
    )
    
    return response.choices[0].message.content, links

# --- Dibakar AI UI ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# চ্যাট হিস্ট্রি দেখানো
for chat in st.session_state.messages:
    if chat["role"] == "user":
        st.markdown(f'<div class="user-msg">{chat["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-msg">{chat["content"]}</div>', unsafe_allow_html=True)
        if "links" in chat:
            st.markdown('<div class="source-container">', unsafe_allow_html=True)
            for i, link in enumerate(chat["links"]):
                logo_url, domain = get_domain_logo(link)
                st.markdown(f'<a href="{link}" target="_blank" class="source-tag"><img src="{logo_url}"> Source [{i+1}] - {domain}</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# চ্যাট ইনপুট বক্স
if prompt := st.chat_input("Ask me anything about IPL 2026, Players, News..."):
    # ইউজার মেসেজ সেভ করা
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)

    # এআই রেসপন্স
    with st.spinner("Analyzing..."):
        answer, sources = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer, "links": sources})
        st.rerun() # স্ক্রিন রিফ্রেশ করে মেসেজগুলো সাজানোর জন্য
