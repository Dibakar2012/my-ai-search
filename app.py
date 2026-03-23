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
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200: return ""
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside']): tag.decompose()
        return " ".join(soup.get_text().split())[:3000]
    except: return ""

def get_ai_response(user_input):
    # --- Greeting Logic ---
    greetings = ["hi", "hii", "hello", "hey", "kaise ho", "kemon acho", "namaste", "হেই", "হ্যালো"]
    user_lower = user_input.lower().strip()
    
    # ছোট মেসেজ বা গ্রিটিং হলে সার্চ বন্ধ রাখবে
    is_greeting = user_lower in greetings or len(user_lower) < 4
    
    context = ""
    links = []

    if not is_greeting:
        search_res = requests.post("https://google.serper.dev/search", 
                                   headers={'X-API-KEY': SERPER_API_KEY}, 
                                   json={"q": user_input, "num": 5}).json()
        
        for item in search_res.get('organic', []):
            link = item['link']
            content = clean_scrape(link)
            if content and "access denied" not in content.lower():
                links.append(link)
                context += f"\nSource: {link}\nContent: {content}\n"

    # --- System Prompt (The Personality) ---
    system_instruction = f"""
    You are Dibakar's Infinite Vision Engine.
    1. STRICT RULE: Respond in the SAME LANGUAGE style as the user. 
    2. If user says 'Hi' or 'Hii', respond like: "Hii! Main thik hoon, aap kaise ho?" or "Hii! আমি ভালো আছি, তুমি কেমন আছো?" 
    3. DO NOT give long definitions of greetings. Be short and friendly for casual chat.
    4. For factual questions (like IPL, players, news), combine web data with your smart knowledge.
    5. Never say "Access Denied". If a site is blocked, just use your own brain to answer.
    6. Use a mix of local language and English terms to look professional.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nUser Question: {user_input}"}
        ],
        temperature=0.8 # একটু ক্রিয়েটিভ উত্তরের জন্য
    )
    
    return response.choices[0].message.content, links

# --- Streamlit UI ---
st.set_page_config(page_title="Dibakar AI Engine", layout="wide")

st.title("🚀 Dibakar's Infinite Vision Engine")
st.write("Smart Hybrid Search | Real-time Data | Friendly Chat")

query = st.text_input("এখানে টাইপ করো (Ask me anything):")

if query:
    with st.spinner('Wait standard processing...'):
        answer, sources = get_ai_response(query)
        st.subheader("🤖 Response")
        st.write(answer)
        
        if sources:
            with st.expander("Reference Data Sources"):
                for url in sources:
                    st.write(f"🔗 {url}")
