import streamlit as st
from transformers import pipeline
import torch

st.title("Welcome to ChristianChat.AI")
st.image("https://static.vecteezy.com/system/resources/previews/027/819/697/large_2x/open-bible-with-sunlights-free-photo.jpg")
st.markdown("---")

@st.cache_resource
def load_ai_model():

return pipeline("text-generation", model="microsoft/Phi-3-mini-4k-instruct", torch_dtype="auto", device_map="auto")

generator = load_ai_model()

if "messages" not in st.session_state:
st.session_session.messages = [
{"role": "assistant", "content": "Hello! Blessings to you. How can I support, encourage, or pray for you today?"}
]
for message in st.session_state.messages:
with st.chat_message(message["role"]):
st.markdown(message["content"])

if user_input := st.chat_input("How can I help or pray for you today my brother/sister?"):
with st.chat_message("user"):
st.markdown(user_input)
st.session_state.messages.append({"role": "user", "content": user_input})
system_instruction = (
"You are a compassionate, and empathetic christian chat assistant. When the user talks about their problems like immigration, stress, or family issues, try to give a raw and empathetic answer. Provide a bible verse relating to their problemsad also make sure to give them a prayer. Try to use the bible for revelance to their problems. Provide them encouragement too."
)

full_prompt = f"System: {system_instruction}\nUser: {user_input}\nAssistant:"
with st.chat_message("assistant"):
with st.spinner("Analyzing...."):
outputs = generator(full_prompt, max_new_tokens=150, do_sample=True, temperature=0.7)
bot_response = outputs[0]['generated_text'].split("Assistant:")[-1].strip()
st.markdown(bot_response)

st.session_state.messages.append({"role": "assistant", "content": bot_response})
