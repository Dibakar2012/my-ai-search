import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# Secrets থেকে API Key লোড করা
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("API Keys missing in Streamlit Secrets!")
    st.stop()

client = Groq(api_key=GROQ_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

def clean_scrape(url):
    """ওয়েবসাইট থেকে পরিষ্কার টেক্সট সংগ্রহ"""
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
    # ধাপ ১: AI ঠিক করবে এই প্রশ্নের জন্য কি ইন্টারনেট সার্চ লাগবে?
    decision_prompt = f"""
    Analyze the user input: "{user_input}"
    Does this question require real-time web search or live data (like news, weather, latest tech, or facts)? 
    Answer only 'YES' or 'NO'.
    """
    decision_res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": decision_prompt}],
        max_tokens=5
    ).choices[0].message.content.strip().upper()

    context = ""
    links = []

    # ধাপ ২: যদি 'YES' হয়, তবেই সার্চ হবে
    if "YES" in decision_res:
        with st.spinner('ইন্টারনেট থেকে তথ্য খোঁজা হচ্ছে...'):
            search_res = requests.post("https://google.serper.dev/search", 
                                       headers={'X-API-KEY': SERPER_KEY}, 
                                       json={"q": user_input, "num": 3}).json()
            
            for item in search_res.get('organic', []):
                link = item['link']
                links.append(link)
                content = clean_scrape(link)
                context += f"\nSource: {link}\nContent: {content}\n"

    # ধাপ ৩: ফাইনাল উত্তর তৈরি (নিজের নলেজ + ওয়েব ডাটা)
    system_instruction = """
    You are a smart AI assistant. 
    1. Respond in the SAME LANGUAGE as the user's question.
    2. If web context is provided, combine it with your internal knowledge to give a better answer.
    3. If no web context is provided, answer using your internal knowledge (for greetings like Hi, Hello).
    4. If using web context, cite sources as [1], [2].
    """
    
    final_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Web Context: {context}\n\nUser Question: {user_input}"}
        ],
        temperature=0.6
    )
    
    return final_response.choices[0].message.content, links

# --- Streamlit UI ---
st.set_page_config(page_title="Smart AI Search", page_icon="🤖")
st.title("🤖 Dibakar's Smart AI Search")
st.caption("অটোমেটিক ওয়েব সার্চ এবং চ্যাটিং মোড সক্রিয়")

query = st.text_input("এখানে লিখুন (Ask me anything):")

if query:
    answer, sources = get_ai_response(query)
    st.markdown(f"**উত্তর:**\n{answer}")
    
    if sources:
        st.sidebar.markdown("### সূত্রসমূহ (Sources):")
        for i, url in enumerate(sources, 1):
            st.sidebar.markdown(f"**[{i}]** [{url}]({url})")
