import streamlit as st
import os
from groq import Groq
from streamlit_mic_recorder import mic_recorder


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
bible_version = st.sidebar.selectbox("Select Version", ["KJV", "NIV", "ESV", "NKJV"])
book_and_chapter = st.sidebar.text_input("Enter Book & Chapter", placeholder="e.g., Philippians 4, Psalms 23")

if st.sidebar.button("📚 Pull Up The Scripture", use_container_width=True):
    if book_and_chapter:
        with st.spinner(f"Searching for {book_and_chapter}..."):
            try:
                bible_prompt = f"Provide the full text for {book_and_chapter} in the {bible_version} version. Only provide the scripture verses with their numbers, formatted cleanly. Do not write any introduction or commentary."
                bible_completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": bible_prompt}],
                    temperature=0.2,
                    max_tokens=5500
                )
                scripture_result = bible_completion.choices[0].message.content.strip()
                st.sidebar.success(f"**{book_and_chapter} ({bible_version})**")
                st.sidebar.markdown(scripture_result)
            except Exception as e:
                st.sidebar.error(f"Could not retrieve scripture: {e}")
    else:
        st.sidebar.warning("Please enter a book and chapter first!")

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


st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f'<div class="bubble user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "assistant":
        st.markdown(f'<div class="bubble assistant-bubble">{message["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
