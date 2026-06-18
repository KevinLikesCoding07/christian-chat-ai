import streamlit as st
import os
from groq import Groq
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io

st.set_page_config(page_title="ChristianChat AI", page_icon="🙏", layout="centered")

st.title("Welcome to ChristianChat.AI")
st.image("https://static.vecteezy.com/system/resources/previews/027/819/697/large_2x/open-bible-with-sunlights-free-photo.jpg")
st.markdown("---")

try:
    client = Groq()
except Exception as e:
    st.error("API Key missing or invalid. Please check your Hugging Face Space Secrets.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

if "total_chats" not in st.session_state:
    if os.path.exists("chat_count.txt"):
        with open("chat_count.txt", "r") as f:
            try:
                st.session_state.total_chats = int(f.read().strip())
            except:
                st.session_state.total_chats = 0
    else:
        st.session_state.total_chats = 0


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
                import requests
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
                    st.session_state.last_viewed_scripture = scripture_text
                else:
                    st.error("Could not reach the Bible database. Please try again.")
            except Exception as e:
                st.error(f"Could not retrieve scripture: {e}")

st.sidebar.markdown("---")
st.sidebar.metric(label="🙏 Total Prayers & Chats", value=st.session_state.total_chats)
st.sidebar.markdown("---")


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
st.markdown("### 🎙️ Or Speak Your Prayer Request:")
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
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    st.session_state.total_chats += 1
    with open("chat_count.txt", "w") as f:
        f.write(str(st.session_state.total_chats))
        
    system_instruction = (
        "You are a compassionate and empathetic Christian chat assistant. When the user talks about "
        "their problems like immigration, stress, or family issues, try to give a raw and empathetic answer. "
        "Provide a real, highly accurate bible verse relating to their problems and also make sure to give them a prayer. "
        "Try to use the bible for relevance to their problems. Encourage them too."
    )
    
    context_scripture = ""
    lower_prompt = active_prompt.lower()
    
    for book in bible_books_with_chapters.keys():
        if book.lower() in lower_prompt:
            import re
            match = re.search(r'\b\d+\b', lower_prompt)
            chapter_to_pull = match.group(0) if match else "1"
            
            try:
                search_prompt = (
                    f"Provide ONLY the official, actual scripture text for {book} chapter {chapter_to_pull}. "
                    f"Do not include any verses from other chapters. Do not include summaries, introductory text, "
                    f"genealogies from other sections, or notes. Start immediately with verse 1 of chapter {chapter_to_pull}."
                )
                context_completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": search_prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                context_scripture = f"\n\n[VERIFIED SCRIPTURE CONTEXT for {book} {chapter_to_pull}]:\n" + context_completion.choices[0].message.content.strip()
                break
            except:
                pass

    api_messages = [{"role": "system", "content": system_instruction}]
    for msg in st.session_state.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
            
    with st.spinner("Connecting to secure prayer network..."):
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=api_messages,
                temperature=0.7,
                max_tokens=5500
            )
            bot_response = completion.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
        except Exception as e:
            st.error(f"API Error: {e}")

st.markdown("""<style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 20px;
    }
    .bubble {
        max-width: 75%;
        padding: 12px 16px;
        border-radius: 20px;
        font-size: 16px;
        line-height: 1.4;
        display: inline-block;
    }
    .user-bubble {
        background-color: #007aff;
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
        text-align: left;
    }
    .assistant-bubble {
        background-color: #f1f0f0;
        color: #1c1c1e;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        text-align: left;
    }
</style>""", unsafe_allow_html=True)

# --- Render Chat History and Audio Players ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f'<div class="bubble user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "assistant":
        st.markdown(f'<div class="bubble assistant-bubble">{message["content"]}</div>', unsafe_allow_html=True)
        
       
        final_lang = 'en'
        try:
            from langdetect import detect
            import gtts.lang
            
            google_languages = gtts.lang.tts_langs()
            raw_detected = detect(message["content"])
            if raw_detected:
                detected_lang = str(raw_detected).strip().lower()
                base_lang = detected_lang.split('-')[0]
                
                if detected_lang in google_languages:
                    final_lang = detected_lang
                elif base_lang in google_languages:
                    final_lang = base_lang
        except Exception as lang_e:
            final_lang = 'en'
            
       
        try:
            audio_buffer = io.BytesIO()
            tts = gTTS(text=message["content"], lang=final_lang, tld='com')
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            st.audio(audio_buffer, format="audio/mp3")
        except Exception as tts_error:
            st.error(f"TTS Error on message {idx}: {tts_error}")

st.markdown('</div>', unsafe_allow_html=True)
