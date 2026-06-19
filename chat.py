import streamlit as st
import os
import io
import hashlib
import json
import re
import requests
from groq import Groq
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
from langdetect import detect
import gtts.lang

st.set_page_config(page_title="ChristianChat AI", page_icon="🙏", layout="centered")

USER_DB_FILE = "users.json"

def load_users():            
    if not os.path.exists(USER_DB_FILE):                
        default_db = {                        
            "admin": hashlib.sha256("ChangeMe123!".encode()).hexdigest()                
        }                
        with open(USER_DB_FILE, "w") as f:                        
            json.dump(default_db, f, indent=4)                
        return default_db                
    try:                
        with open(USER_DB_FILE, "r") as f:                        
            return json.load(f)        
    except Exception:                
        return {}

def save_user(username, password_hash):        
    """Saves a new user to the JSON database."""        
    users = load_users()        
    users[username] = password_hash        
    with open(USER_DB_FILE, "w") as f:                
        json.dump(users, f, indent=4)

def hash_password(password):        
    """Securely hash passwords so they aren't stored in plain text."""        
    return hashlib.sha256(password.encode()).hexdigest()

if "connected" not in st.session_state:        
    st.session_state.connected = False
if "messages" not in st.session_state:        
    st.session_state.messages = []
if "preset_prompt" not in st.session_state:        
    st.session_state.preset_prompt = None
if "total_chats" not in st.session_state:        
    if os.path.exists("chat_count.txt"):                
        with open("chat_count.txt", "r") as f:                        
            try:                                
                st.session_state.total_chats = int(f.read().strip())                        
            except Exception:                                
                st.session_state.total_chats = 0        
    else:                
        st.session_state.total_chats = 0

if not st.session_state.connected:        
    st.title("Welcome to ChristianChat AI")        
    st.image("https://static.vecteezy.com/system/resources/previews/027/819/697/large_2x/open-bible-with-sunlights-free-photo.jpg")        
    st.markdown("---")            
    user_db = load_users()        
    auth_mode = st.radio("Choose Action", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")                
    
    if auth_mode == "Sign In":                
        st.subheader("🔐 Secure Private Sanctuary")                
        with st.form("login_form"):                        
            username = st.text_input("Username").strip().lower()                        
            password = st.text_input("Password", type="password")                        
            submit_button = st.form_submit_button("Sign In", use_container_width=True)                                    
            if submit_button:                                
                if not username or not password:                                        
                    st.error("Please fill out all fields.")                                
                elif username in user_db and user_db[username] == hash_password(password):                                        
                    st.session_state.connected = True                                        
                    st.session_state.user_info = {"name": username.capitalize()}                                        
                    st.success("Access Granted!")                                        
                    st.rerun()                                
                else:                                        
                    st.error("Invalid username or password.")                                
    elif auth_mode == "Create Account":                
        st.subheader("✨ Create Your Account")                
        with st.form("register_form"):                        
            new_username = st.text_input("Choose a Username").strip().lower()                        
            new_password = st.text_input("Choose a Password", type="password")                        
            confirm_password = st.text_input("Confirm Your Password", type="password")                        
            register_button = st.form_submit_button("Register Account", use_container_width=True)                                    
            if register_button:                                
                if not new_username or not new_password:                                        
                    st.error("Fields cannot be left blank.")                                
                elif new_username in user_db:                                        
                    st.error("That username is already taken. Please pick another one.")                                
                elif new_password != confirm_password:                                        
                    st.error("Passwords do not match.")                                
                elif len(new_password) < 6:                                        
                    st.error("Password must be at least 6 characters long.")                                
                else:                                        
                    hashed_pwd = hash_password(new_password)                                        
                    save_user(new_username, hashed_pwd)                                        
                    st.success("Account created successfully! Drop down to 'Sign In' above to log in.")        
    st.stop()

try:        
    client = Groq()
except Exception as e:        
    st.error("API Key missing or invalid. Please check your Hugging Face Space Secrets.")        
    st.stop()

st.sidebar.title(f"🙏 Welcome, {st.session_state.user_info['name']}!")
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Log Out", use_container_width=True):        
    st.session_state.connected = False        
    st.session_state.messages = []        
    if 'user_info' in st.session_state:                
        del st.session_state['user_info']        
    st.rerun()

st.sidebar.title("📖 Bible Scripture")
bible_version = st.sidebar.selectbox("Select Version", ["KJV", "NIV", "ESV", "NKJV", "WEB"])
bible_books_with_chapters = {        
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34, "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 samuel": 24, "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29,        
    "2 Chronicles": 36, "Ezra": 10, "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31, "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52, "Lamentations": 5,        
    "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4,         
    "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28, "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6, "Ephesians": 6, "Philippians": 4, "Colossians": 4,         
    "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3, "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5, "2 John": 1,         
    "3 John": 1, "Jude": 1, "Revelation": 22
}
selected_book = st.sidebar.selectbox("Pick a Book", list(bible_books_with_chapters.keys()))
max_chapters = bible_books_with_chapters[selected_book]
st.sidebar.write("👉 **Select a Chapter:**")

cols = st.sidebar.columns(4)
chosen_chapter = None
for i in range(1, max_chapters + 1):        
    col_index = (i - 1) % 4        
    with cols[col_index]:                
        if st.button(str(i), key=f"btn_ch_{i}", use_container_width=True):                        
            chosen_chapter = i

if chosen_chapter is not None:        
    book_and_chapter = f"{selected_book} {chosen_chapter}"        
    with st.sidebar:                
        with st.spinner(f"Pulling up {book_and_chapter}..."):                        
            try:                                
                version_map = {"KJV": "kjv", "NIV": "web", "ESV": "web", "NKJV": "web", "WEB": "web"}                                
                api_version = version_map.get(bible_version, "kjv")                                
                url = f"https://bible-api.com/{selected_book}+{chosen_chapter}?translation={api_version}"                                
                response = requests.get(url)                                                
                if response.status_code == 200:                                        
                    data = response.json()                                        
                    scripture_text = ""                                        
                    for verse in data["verses"]:                                                
                        scripture_text += f"**{verse['verse']}** {verse['text'].strip()}\n\n"                    
                    st.success(f"**{book_and_chapter} ({bible_version})**")                    
                    st.markdown(scripture_text)                
                else:                                        
                    st.error("Could not reach the Bible database.")                        
            except Exception as e:                                
                st.error(f"Could not retrieve scripture: {e}")

st.sidebar.markdown("---")
st.sidebar.metric(label="🙏 Total Prayers & Chats", value=st.session_state.total_chats)

st.title("Welcome to ChristianChat.AI")
st.image("https://static.vecteezy.com/system/resources/previews/027/819/697/large_2x/open-bible-with-sunlights-free-photo.jpg")
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello! It's wonderful to connect with you. How can I pray for you today my brother/sister?", 
        "audio": None
    })
st.markdown("---")
st.html("""
<style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 14px;
        margin-bottom: 25px;
        padding: 10px;
        width: 100%;
    }
    .msg-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 75%;
    }
    .user-wrapper {
        align-self: flex-end;
        align-items: flex-end;
        margin-left: auto;
    }
    .assistant-wrapper {
        align-self: flex-start;
        align-items: flex-start;
        margin-right: auto;
    }
    .sender-name {
        font-size: 12px;
        color: #8e8e93;
        margin-bottom: 4px;
        margin-left: 6px;
        margin-right: 6px;
        font-weight: 500;
    }
    .bubble {
        padding: 14px 18px;
        border-radius: 20px;
        font-size: 16px;
        line-height: 1.45;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .user-bubble {
        background: linear-gradient(135deg, #007aff, #0055d4) !important;
        color: white !important;
        border-bottom-right-radius: 4px;
    }
    .assistant-bubble {
        background-color: #f1f0f0 !important;
        color: #1c1c1e !important;
        border-bottom-left-radius: 4px;
        border: 1px solid #e5e5ea;
    }
</style>
""")


st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.messages:    
   
    display_text = message["content"]
    
    if message["role"] == "user":                
        display_name = st.session_state.user_info['name']                
        st.markdown(f'''                        
            <div class="msg-wrapper user-wrapper">                                
                <span class="sender-name">👤 {display_name}</span>                                
                <div class="bubble user-bubble">{display_text}</div>                        
            </div>                
        ''', unsafe_allow_html=True)        
    elif message["role"] == "assistant":                
        st.markdown(f'''                        
            <div class="msg-wrapper assistant-wrapper">                                
                <span class="sender-name">🕊️ Assistant</span>                                
                <div class="bubble assistant-bubble">{display_text}</div>                        
            </div>                
        ''', unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)

    
          

for idx, msg in enumerate(st.session_state.messages):        
    if msg["role"] == "assistant":                
        if msg.get("audio") is not None:                        
            st.audio(msg["audio"], format="audio/mp3")                
        elif idx == len(st.session_state.messages) - 1:                        
            st.caption("🔊 Audio clip generation paused due to safe rate limits.")

st.markdown("---")


st.markdown("### 💡 Need prayer or guidance right now? Click a topic:")
col1, col2, col3 = st.columns(3)
with col1:        
    if st.button("Stress", use_container_width=True):                
        st.session_state.preset_prompt = "I'm feeling really stressed and overwhelmed by everything."
with col2:        
    if st.button("Relationships", use_container_width=True):                
        st.session_state.preset_prompt = "I need some biblical guidance on dealing with relationship issues."
with col3:        
    if st.button("Daily Guidance", use_container_width=True):                
        st.session_state.preset_prompt = "I just need daily guidance and a general prayer."

st.markdown("---")
st.markdown("### Record your voice:")
if "prayer_mic_output" not in st.session_state:
    st.session_state.prayer_mic_output = None

audio = mic_recorder(        
    start_prompt="🎵 Start Recording",        
    stop_prompt="🛑 Stop Recording",        
    just_once=True,        
    key="prayer_mic"
)

user_input = st.chat_input("How can I help or pray for you today my brother/sister?", key="main_chat_input")
active_prompt = None

if st.session_state.preset_prompt:        
    active_prompt = st.session_state.preset_prompt        
    st.session_state.preset_prompt = None  
elif user_input:        
    active_prompt = user_input
elif audio is not None:        
    audio_bytes = audio['bytes']        
    if len(audio_bytes) > 0:                
        with st.spinner("Translating your voice into text..."):                        
            try:                                
                with open("temp_audio.wav", "wb") as f:                                        
                    f.write(audio_bytes)                                
                with open("temp_audio.wav", "rb") as audio_file:                                        
                    transcription = client.audio.transcriptions.create(                                                
                        model="whisper-large-v3",                                                 
                        file=audio_file                                        
                    )                                
                active_prompt = transcription.text                                
                st.success(f"🗣️ Heard: \"{active_prompt}\"")                                
                os.remove("temp_audio.wav")                        
            except Exception as e:                                
                st.error(f"Voice processing error: {e}")

if active_prompt is not None:        
    st.session_state.messages.append({"role": "user", "content": active_prompt, "audio": None})        
    st.session_state.total_chats += 1        
    with open("chat_count.txt", "w") as f:                
        f.write(str(st.session_state.total_chats))                    
    
    system_instruction = (                
        "You are a compassionate and empathetic Christian chat assistant. When the user talks about "                
        "their problems like immigration, stress, or family issues, try to give a raw and empathetic answer. "                
        "Provide a real, highly accurate bible verse relating to their problems and also make sure to give them a prayer. "                
        "Try to use the bible for relevance to their problems. Encourage them too."        
    )                
    
    api_messages = [{"role": "system", "content": system_instruction}]        
    for msg in st.session_state.messages:                
        api_messages.append({"role": msg["role"], "content": msg["content"]})                    
    
    with st.spinner("Connecting to secure prayer network..."):                
        try:                        
            completion = client.chat.completions.create(                                
                model="llama-3.1-8b-instant",                                
                messages=api_messages,                                
                temperature=0.7,                                
                max_tokens=2000                        
            )                        
            bot_response = completion.choices[0].message.content.strip()                                                
            
            audio_bytes = None                        
            try:                                
                final_lang = 'en'                                
                try:                                        
                    google_languages = gtts.lang.tts_langs()                                        
                    raw_detected = detect(bot_response)                                        
                    if raw_detected:                                                
                        detected_lang = str(raw_detected).strip().lower()                                                
                        base_lang = detected_lang.split('-')[0]                                                
                        if detected_lang in google_languages:                                                        
                            final_lang = detected_lang                                                
                        elif base_lang in google_languages:                                                        
                            final_lang = base_lang                                
                except Exception:                                        
                    final_lang = 'en'                                                
                
                audio_buffer = io.BytesIO()                                
                shortened_text = bot_response[:300]                                  
                tts = gTTS(text=shortened_text, lang=final_lang, tld='com')                                
                tts.write_to_fp(audio_buffer)                                
                audio_bytes = audio_buffer.getvalue()                        
            except Exception:                                
                audio_bytes = None                                     
            
            st.session_state.messages.append({"role": "assistant", "content": bot_response, "audio": audio_bytes})                        
            st.rerun()                            
        except Exception as e:                        
            st.error(f"API Error: {e}")

   
