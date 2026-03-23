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

# --- UI Layout & Advanced Premium CSS ---
st.set_page_config(page_title="Dibakar AI", layout="centered")

st.markdown("""
    <style>
    /* মেইন ব্যাকগ্রাউন্ড (Darker, Premium Deep Navy) */
    .stApp {
        background-color: #070B16; 
        color: #E2E8F0;
    }
    
    /* টাইটেল ডিজাইন (Premium Gradient & Glow) */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 2.5rem;
        background: linear-gradient(to right, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(96, 165, 250, 0.4);
        font-family: 'Segoe UI', system-ui, sans-serif;
    }

    /* নতুন চ্যাট ইনপুট ফিক্স - এটিকে টেক্সট বক্সের ভেতর আনা */
    .stChatInput {
        background-color: #121827 !important;
        border-radius: 20px !important;
        padding: 10px !important;
        border: 2px solid #2D3748 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        transition: 0.3s;
        margin-bottom: 20px;
    }
    .stChatInput:focus-within {
        border-color: #60A5FA !important;
        box-shadow: 0 0 20px rgba(96, 165, 250, 0.2) !important;
    }
    /* ইনপুট ফিল্ডের কালার */
    .stChatInput > div > div > textarea {
        color: white !important;
        font-size: 16px !important;
    }
    /* সেন্ট আইকনের কালার ফিক্স */
    .stChatInput button {
        color: #60A5FA !important;
    }

    /* রেসপন্স কন্টেইনার (Modern Perplexity Style) */
    .response-container {
        background-color: #121827;
        border-radius: 15px;
        padding: 25px;
        margin-top: 30px;
        border: 1px solid #2D3748;
        line-height: 1.8;
        font-family: 'SF Pro Display', sans-serif;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* সোর্স হেডার */
    .source-header {
        color: #94A3B8;
        margin-top: 25px;
        font-weight: 600;
        font-size: 1.1rem;
    }
    /* সোর্স কার্ড */
    .source-card {
        background-color: #1A2132;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #2D3748;
        font-size: 14px;
        transition: 0.2s ease-in-out;
    }
    .source-card:hover {
        border-color: #60A5FA;
        background-color: #2D3748;
        transform: translateY(-2px);
    }
    
    /* Hide Streamlit Header/Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Logic Functions (Fixed Garbage Logic) ---
def clean_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200: return ""
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside', 'ads', 'form', 'button', 'ul', 'ol']): tag.decompose()
        text = " ".join(soup.get_text().split())
        return text[:1500]
    except: return ""

def remove_garbage_patterns(text):
    cleaned = re.sub(r'(\d+[ms]\s+\d+[ms]\s*·*)+', '', text) 
    cleaned = re.sub(r'(\s*·*\s*0\s*·*)+', '', cleaned)
    return cleaned.strip()

def get_ai_response(user_input):
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
            link = item['link']
            item_snippet = remove_garbage_patterns(item.get('snippet', ''))
            content = clean_scrape(link)
            cleaned_content = remove_garbage_patterns(content)
            
            if len(cleaned_content) > 100 and "access denied" not in cleaned_content.lower():
                links.append(link)
                context += f"\nSource: {link}\nSearch Snippet: {item_snippet}\nWebsite Content: {cleaned_content}\n"

    system_instruction = f"""
    You are Dibakar AI, a professional research engine. Match the user's language style.
    Combine internal knowledge with the provided context. Prioritize accuracy over length.
    Never mention access denied or gibberish repetitions in response.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nQuestion: {user_input}"}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content, links

# --- Dibakar AI UI ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# সেন্টারে ইনপুট বক্স আনার জন্য (Columns removed, centered layout used)
# এটিই সবথেকে বড় পরিবর্তন
query = st.chat_input("Ask about anything... (IPL, News, etc.)")

if query:
    with st.spinner('Accessing infinite knowledge...'):
        answer, sources = get_ai_response(query)
        
        # রেসপন্স বক্স
        st.markdown(f'<div class="response-container">{answer}</div>', unsafe_allow_html=True)
        
        # সোর্স কার্ড
        if sources:
            st.markdown('<div class="source-header">🌐 Verified Sources</div>', unsafe_allow_html=True)
            for url in sources:
                st.markdown(f'<div class="source-card">🔗 <a href="{url}" target="_blank" style="color:#60A5FA; text-decoration:none;">{url}</a></div>', unsafe_allow_html=True)
