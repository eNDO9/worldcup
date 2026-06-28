import streamlit as st
from supabase_client import get_client

st.set_page_config(page_title="World Cup", layout="wide")
st.title("World Cup App")

supabase = get_client()

st.success("Connected to Supabase!")
