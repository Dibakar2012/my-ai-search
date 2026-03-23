import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Secrets Management
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API Keys missing! Please set them in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

def clean_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return "" # Agar site block kare toh empty string return karo
        
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside']):
            tag.decompose()
        
        text = " ".join(soup.get_text().split())
        return text[:3000]
    except:
        return ""

def get_ai_response(user_input):
    # Search for data
    search_res = requests.post("https://google.serper.dev/search", 
                               headers={'X-API-KEY': SERPER_KEY}, 
                               json={"q": user_input, "num": 5}).json()
    
    context = ""
    links = []
    
    for item in search_res.get('organic', []):
        link = item['link']
        content = clean_scrape(link)
        if content and "access denied" not in content.lower():
            links.append(link)
            context += f"\nSource: {link}\nContent: {content}\n"

    # AI Instruction: Yahan hum "Access Denied" wali baatein rok rahe hain
    system_instruction = f"""
    You are Dibakar's Infinite Vision AI. 
    1. Respond in the SAME LANGUAGE as the user.
    2. Use the provided Web Context + your own massive training data.
    3. IMPORTANT: Never mention "Access Denied", "I cannot visit the link", or "Forbidden" to the user. 
    4. If a website is blocked, ignore it and answer based on other sources and your internal knowledge.
    5. For IPL 2026 or sports, provide specific dates, player names, and team details clearly.
    6. Keep the tone professional and helpful.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nUser Question: {user_input}"}
        ],
        temperature=0.5
    )
    
    return response.choices[0].message.content, links

# --- UI Layout ---
st.set_page_config(page_title="Dibakar AI Engine", layout="wide")

st.title("🚀 Dibakar's Infinite Vision Engine")
st.info("System Status: Online | Processing with Llama 3.1 128k Context")

query = st.text_input("Ask about IPL 2026, Players, or anything:")

if query:
    with st.spinner('Analyzing real-time data...'):
        answer, sources = get_ai_response(query)
        
        st.markdown("### 🤖 Engine Response")
        st.write(answer)
        
        if sources:
            with st.expander("Verified Data Sources"):
                for url in sources:
                    st.write(f"🔗 {url}")
