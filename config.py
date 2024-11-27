import streamlit as st
from openai import OpenAI

def init_openai_client():
    """Initialize OpenAI client with API key"""
    api_key = st.session_state.get('OPENAI_API_KEY')
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def check_api_key():
    """Check if API key is configured"""
    return 'OPENAI_API_KEY' in st.session_state
