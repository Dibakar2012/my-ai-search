import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# 1. Secrets Management (Make sure these names match Streamlit Cloud Secrets)
try:
    # यहाँ हम secrets से डेटा ले रहे हैं
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API Keys missing! Please add SERPER_API_KEY and GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

# 2. Client Setup (अब GROQ_API_KEY सही से काम करेगा)
client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

def clean_scrape(url):
    """Web scraping with better headers to avoid access denied"""
    try:
        # Real browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return ""
        
        soup = BeautifulSoup(res.content, 'html.parser')
        # Remove junk
        for tag in soup(['nav', 'footer', 'script', 'style', 'header', 'aside']):
            tag.decompose()
        
        text = " ".join(soup.get_text().split())
        return text[:4000]
    except:
        return ""

def get_ai_response(user_input):
    # Search for real-time data
    search_res = requests.post(
        "https://google.serper.dev/search", 
        headers={'X-API-KEY': SERPER_API_KEY}, 
        json={"q": user_input, "num": 5}
    ).json()
    
    context = ""
    links = []
    
    for item in search_res.get('organic', []):
        link = item['link']
        content = clean_scrape(link)
        # Filter out obvious 'Access Denied' text
        if content and "access denied" not in content.lower() and "forbidden" not in content.lower():
            links.append(link)
            context += f"\nSource: {link}\nContent: {content}\n"

    # System Prompt for IPL and general chat
    system_instruction = """
    You are Dibakar's Infinite Vision Engine.
    1. Respond in the same language as the user.
    2. Combine Web Context with your internal knowledge.
    3. NEVER mention "Access Denied" or "I cannot visit the link".
    4. If web data is missing, use your internal training data to answer accurately (especially for IPL 2026).
    5. Be friendly and professional.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nQuestion: {user_input}"}
        ],
        temperature=0.6
    )
    
    return response.choices[0].message.content, links

# --- Streamlit UI ---
st.set_page_config(page_title="Dibakar AI Engine", layout="wide")

st.title("🚀 Dibakar's Infinite Vision Engine")
st.markdown("---")

query = st.text_input("Ask me anything (IPL, News, or just say Hi):")

if query:
    with st.spinner('Processing your request...'):
        answer, sources = get_ai_response(query)
        
        st.subheader("🤖 Engine Response")
        st.write(answer)
        
        if sources:
            with st.expander("Reference Links"):
                for url in sources:
                    st.write(f"🔗 {url}")
