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
    # --- Greeting & Language Logic ---
    greetings = ["hi", "hii", "hello", "hey", "kaise ho", "kemon acho", "namaste", "কেমন আছো", "কেমন আছ"]
    user_lower = user_input.lower().strip()
    
    # Check if search is really needed
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

    # --- Strict System Prompt ---
    system_instruction = f"""
    You are Dibakar's Infinite Vision Engine.
    STRICT RULES:
    1. LANGUAGE: Respond ONLY in the language used by the user. 
       - If User says "Kaise ho" (Hindi), answer ONLY in Hindi (e.g., "Main theek hoon").
       - If User says "Kemon acho" (Bengali), answer ONLY in Bengali (e.g., "Ami bhalo achi").
       - If User says "Hi" (English), answer in English.
    2. NO REPETITION: Do not repeat time stamps like '10m 34s' or any gibberish data.
    3. GREETINGS: If it's a greeting, DO NOT use web search results about songs or companies. Just answer like a human friend.
    4. KNOWLEDGE: For real questions, mix web data with your own brain. Never mention technical errors like 'Access Denied'.
    5. PERSONALITY: Be smart, direct, and professional. Use English technical terms only where necessary.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nUser Input: {user_input}"}
        ],
        temperature=0.3 # কমিয়ে দেওয়া হয়েছে যাতে ভুলভাল কথা না বলে (Less creative, more accurate)
    )
    
    return response.choices[0].message.content, links

# --- Streamlit UI ---
st.set_page_config(page_title="Dibakar AI Engine", layout="wide")

st.title("🚀 Dibakar's Infinite Vision Engine")
st.write("Smart Language Detection | Real-time Search | Hybrid AI")

query = st.text_input("এখানে লিখুন (Type here):")

if query:
    with st.spinner('Processing...'):
        answer, sources = get_ai_response(query)
        st.subheader("🤖 Response")
        st.write(answer)
        
        if sources:
            with st.expander("Reference Data Sources"):
                for url in sources:
                    st.write(f"🔗 {url}")
