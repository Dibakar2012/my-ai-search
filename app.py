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

# --- UI Layout & Perplexity Style CSS (Advanced) ---
st.set_page_config(page_title="Dibakar AI", layout="centered") # কেন্দ্রীভূত লেআউট

st.markdown("""
    <style>
    /* মেইন ব্যাকগ্রাউন্ড (Deep Navy Blue) */
    .stApp {
        background-color: #0B1120; 
        color: #F1F5F9;
    }
    
    /* টাইটেল গ্রাডিয়েন্ট */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-top: -50px;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Segoe UI', sans-serif;
    }

    /* সার্চ কন্টেইনার */
    .stTextInput > div > div > input {
        background-color: #161E31 !important;
        color: white !important;
        border: 2px solid #2D3748 !important;
        border-radius: 12px !important;
        padding: 18px 25px !important;
        font-size: 16px !important;
        transition: 0.3s;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #60A5FA !important;
        box-shadow: 0 0 20px rgba(96, 165, 250, 0.2) !important;
    }

    /* বাটন ডিজাইন */
    .stButton > button {
        background-color: #3B82F6 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 10px 25px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover {
        background-color: #2563EB !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5) !important;
    }

    /* রেসপন্স কন্টেইনার */
    .response-container {
        background-color: #161E31;
        border-radius: 15px;
        padding: 25px;
        margin-top: 30px;
        border: 1px solid #2D3748;
        line-height: 1.7;
    }

    /* সোর্স কার্ড */
    .source-header {
        color: #94A3B8;
        margin-top: 25px;
        font-weight: 600;
    }
    .source-card {
        background-color: #1E293B;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #334155;
        font-size: 14px;
        transition: 0.2s;
    }
    .source-card:hover {
        border-color: #60A5FA;
        background-color: #2D3748;
    }
    
    /* Hide Streamlit Header/Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stStatusWidget"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- Session State to handle input clearing ---
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'last_query' not in st.session_state:
    st.session_state['last_query'] = ""

def clean_input():
    # বাটন ক্লিক করার পর টেক্সট বক্স ফাঁকা করার লজিক
    st.session_state['last_query'] = st.session_state.widget_query
    st.session_state.widget_query = ""

# --- Logic Functions (Fixed Logic) ---
def clean_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200: return ""
        soup = BeautifulSoup(res.content, 'html.parser')
        # শুধু মূল লেখা রাখা (অদরকারি সব মুছে ফেলা)
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside', 'ads', 'form', 'button', 'ul', 'ol']): tag.decompose()
        text = " ".join(soup.get_text().split())
        return text[:1500] # খুব বড় লেখা না নেওয়া
    except: return ""

def remove_garbage_patterns(text):
    # ওই লম্বা "0 · 0" বা গানের প্যাটার্ন মুছে ফেলার জন্য ফিল্টার
    # প্যাটার্ন ১: রিপিটেড সংখ্যা এবং চিহ্ন (যেমন: 0 · 0 · 0 বা 10m 34s)
    cleaned = re.sub(r'(\d+[ms]\s+\d+[ms]\s*·*)+', '', text) 
    # প্যাটার্ন ২: শুধু জিরো এবং ডট লুপ
    cleaned = re.sub(r'(\s*·*\s*0\s*·*)+', '', cleaned)
    return cleaned.strip()

def get_ai_response(user_input):
    # ছোট শুভেচ্ছা বাক্য হলে সার্চ অফ রাখা
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
            # প্রথম ফিল্টার: গুগল যে স্নুপেট (Snippet) দেয়, সেটি ক্লিন করা
            item_snippet = remove_garbage_patterns(item.get('snippet', ''))
            
            content = clean_scrape(link)
            # দ্বিতীয় ফিল্টার: ওয়েবসাইটের ভেতর থেকে আসা ডেটা ক্লিন করা
            cleaned_content = remove_garbage_patterns(content)
            
            # ডেটা ফাঁকা বা ব্লক না হলে নেওয়া
            if len(cleaned_content) > 100 and "access denied" not in cleaned_content.lower():
                links.append(link)
                # স্নুপেট এবং মেইন কন্টেন্ট দুটোই দেওয়া যাতে AI সঠিক তথ্য পায়
                context += f"\nSource: {link}\nSearch Snippet: {item_snippet}\nWebsite Content: {cleaned_content}\n"

    # --- Strict System Prompt ---
    system_instruction = f"""
    You are Dibakar AI, a professional research engine.
    1. LANGUAGE: Respond only in the user's language. If they ask in Hinglish or Bengali-English mix, respond in that style.
    2. ANTI-GIBBERISH: If the provided Web Context contains many repeating numbers like '0 · 0 · 0', '10m 34s', or lyrics data, IGNORE IT COMPLETELY. That is junk data from Google.
    3. GREETINGS: If user says 'Kaise ho', DO NOT use web context about songs. Just answer as a friend (e.g., 'Main badhiya hoon, aap batao').
    4. KNOWLEDGE: For factual queries, prioritize internal knowledge if web context looks untrustworthy.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nUser Question: {user_input}"}
        ],
        temperature=0.3 # কমিয়ে দেওয়া হয়েছে যাতে ভুলভাল কথা না বলে
    )
    
    return response.choices[0].message.content, links

# --- Dibakar AI UI Layout ---
st.markdown('<div class="main-title">Dibakar AI</div>', unsafe_allow_html=True)

# টেক্সট বক্স এবং সেন্ড বাটন
input_col, button_col = st.columns([5, 1])
with input_col:
    # widget_query দিয়ে key ট্র্যাক করা হচ্ছে
    st.text_input("", placeholder="Ask me about anything...", label_visibility="collapsed", key="widget_query")

with button_col:
    st.markdown('<div style="margin-top:2px;"></div>', unsafe_allow_html=True)
    submit_btn = st.button("Send", on_click=clean_input) # বাটন ক্লিক করলে clean_input কল হবে

# যখন কেউ প্রশ্ন করবে (last_query তে যখন ডেটা আসবে)
current_query = st.session_state['last_query']

if current_query:
    with st.spinner('Accessing infinite databases...'):
        answer, sources = get_ai_response(current_query)
        
        # রেসপন্স বক্স
        st.markdown(f'<div class="response-container">{answer}</div>', unsafe_allow_html=True)
        
        # সোর্স কার্ড
        if sources:
            st.markdown('<div class="source-header">🌐 Verified Sources</div>', unsafe_allow_html=True)
            for url in sources:
                st.markdown(f'<div class="source-card">🔗 <a href="{url}" target="_blank" style="color:#60A5FA; text-decoration:none; word-break: break-all;">{url}</a></div>', unsafe_allow_html=True)
            st.session_state['last_query'] = "" # উত্তর আসার পর কুয়েরি রিসেট করা
