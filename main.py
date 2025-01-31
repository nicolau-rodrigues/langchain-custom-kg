from orchestration_agent import query_triple_store
import streamlit as st
from streamlit_chat import message

st.header("PoC - Knowledge Graph Chatbot")
st.write("This is a proof of concept for a chatbot that can answer questions about a knowledge graph.")

if "chat_answers_history" not in st.session_state:
    st.session_state["chat_answers_history"] = []
if "user_prompt_history" not in st.session_state:
    st.session_state["user_prompt_history"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

prompt = st.text_input("Prompt")
if st.button("Send"):
    st.session_state["user_prompt_history"].append(prompt)
    st.session_state["chat_history"].append("User: " + prompt)
    
    response = query_triple_store(prompt)
    
    st.session_state["chat_answers_history"].append(response)
    st.session_state["chat_history"].append("Chatbot: " + response)

if st.session_state["chat_answers_history"]:
    st.write("Chat History")
    for i, (user_prompt, chat_response) in enumerate(
        reversed(
            list(
                zip(
                    st.session_state["user_prompt_history"],
                    st.session_state["chat_answers_history"],
                )
            )
        )
    ):
        message(user_prompt, is_user=True, key=f"user_{i}")
        message(chat_response, key=f"bot_{i}")
