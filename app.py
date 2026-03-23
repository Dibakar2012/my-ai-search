import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Secrets ম্যানেজমেন্ট
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API Keys missing! Please set them in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

def clean_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside']):
            tag.decompose()
        return " ".join(soup.get_text().split())[:2500]
    except:
        return ""

def get_ai_response(user_input):
    # ১. ডিসিশন মেকিং: সার্চ লাগবে কি না?
    # গ্রিটিংস বা সাধারণ কথার জন্য সার্চ অফ থাকবে
    greetings = ['hi', 'hello', 'hey', 'kaise ho', 'kemon acho', 'how are you']
    need_search = True
    if any(word in user_input.lower() for word in greetings) and len(user_input.split()) < 4:
        need_search = False

    context = ""
    links = []

    if need_search:
        # জটিল প্রশ্নের জন্য সার্চ
        search_res = requests.post("https://google.serper.dev/search", 
                                   headers={'X-API-KEY': SERPER_KEY}, 
                                   json={"q": user_input, "num": 3}).json()
        
        for item in search_res.get('organic', []):
            link = item['link']
            links.append(link)
            content = clean_scrape(link)
            context += f"\nSource: {link}\nContent: {content}\n"

    # ২. ফাইনাল প্রম্পট (যাতে সে লেকচার না দেয়)
    system_instruction = f"""
    You are a friendly and smart AI assistant. 
    1. Respond in the EXACT same language as the user. If they ask in Hindi-English mix, you answer in Hindi-English mix.
    2. DO NOT explain the meaning of words like 'Kaise ho'. Just answer naturally like a human friend.
    3. Use your internal knowledge + Web Context (if provided).
    4. Keep the UI theme professional: Use some English technical words in your Bengali/Hindi sentences (e.g., 'System update', 'Data search', 'Processing').
    5. If it's a greeting, just say: "I am fine! How can I help you today?" in the user's language.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Context: {context}\n\nUser: {user_input}"}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content, links

# --- Streamlit UI (English Theme) ---
st.set_page_config(page_title="Dibakar AI Engine", layout="wide")

# Custom CSS for English/Professional Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stTextInput { border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Dibakar's Infinite Vision Engine")
st.subheader("Hybrid Intelligence: Live Web + AI Knowledge")

query = st.text_input("Enter your query or just say Hi:")

if query:
    answer, sources = get_ai_response(query)
    
    st.markdown("### 🤖 Response")
    st.write(answer)
    
    if sources:
        with st.expander("View Reference Sources"):
            for i, url in enumerate(sources, 1):
                st.write(f"[{i}] {url}")
