import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# 1. Secrets Management
try:
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API Keys missing! Please add them in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

# --- UI Layout & Perplexity Style CSS ---
st.set_page_config(page_title="Dibakar AI", layout="wide")

st.markdown("""
    <style>
    /* মেইন ব্যাকগ্রাউন্ড */
    .stApp {
        background-color: #0F172A; /* Dark Blue */
        color: #E2E8F0;
    }
    
    /* টাইটেল ডিজাইন */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        background: -webkit-linear-gradient(#60A5FA, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* সার্চ বক্স ডিজাইন (Perplexity Style) */
    .stTextInput > div > div > input {
        background-color: #1E293B !important;
        color: white !important;
        border: 2px solid #334155 !important;
        border-radius: 15px !important;
        padding: 20px !important;
        font-size: 18px !important;
        transition: 0.3s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #60A5FA !important;
        box-shadow: 0 0 15px rgba(96, 165, 250, 0.3) !important;
    }

    /* রেসপন্স বক্স */
    .response-container {
        background-color: #1E293B;
        border-radius: 15px;
        padding: 25px;
        border-left: 5px solid #3B82F6;
        margin-top: 20px;
    }

    /* সোর্স কার্ড ডিজাইন */
    .source-card {
        background-color: #334155;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #475569;
        font-size: 14px;
    }
    
    /* Hide Streamlit Header/Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Logic Functions ---
def clean_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code != 200: return ""
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside', 'ads']): tag.decompose()
        return " ".join(soup.get_text().split())[:2000]
    except: return ""

def get_ai_response(user_input):
    greetings = ["hi", "hii", "hello", "hey", "kaise ho", "kemon acho", "namaste", "কেমন আছো", "কেমন আছ"]
    user_lower = user_input.lower().strip()
    is_greeting = any(greet in user_lower for greet in greetings) and len(user_lower.split()) < 5
    
    context = ""
    links = []

    if not is_greeting:
        search_res = requests.post("https://google.serper.dev/search", 
                                   headers={'X-API-KEY': SERPER_API_KEY}, 
                                   json={"q": user_input, "num": 3}).json()
        
        for item in search_res.get('organic', []):
            link = item['link']
            content = clean_scrape(link)
            if content and "access denied" not in content.lower():
                links.append(link)
                context += f"\nSource: {link}\nContent: {content}\n"

    system_instruction = f"""
    You are Dibakar AI, a professional research assistant.
    1. LANGUAGE: Respond ONLY in the language used by the user.
    2. NO REPETITION: Do not repeat time stamps or gibberish data.
    3. GREETINGS: Answer naturally like a smart friend.
    4. KNOWLEDGE: For real questions, mix web data with your smart brain.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nUser Input: {user_input}"}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content, links

# --- Dibakar AI UI ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# সেন্টারে সার্চ বার আনার জন্য কলম ব্যবহার করা হলো
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    query = st.text_input("", placeholder="Ask anything...", label_visibility="collapsed")

if query:
    with st.spinner('Searching the universe...'):
        answer, sources = get_ai_response(query)
        
        # রেসপন্স এরিয়া
        st.markdown(f'<div class="response-container">{answer}</div>', unsafe_allow_html=True)
        
        # সোর্স কার্ড সাইডবারে বা নিচে
        if sources:
            st.markdown("### 🌐 Sources")
            for url in sources:
                st.markdown(f'<div class="source-card">🔗 <a href="{url}" style="color:#60A5FA; text-decoration:none;">{url}</a></div>', unsafe_allow_html=True)
