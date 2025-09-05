import streamlit as st
from summarizer import summarize_text

st.set_page_config(page_title="Summarizer")

st.title("Summarizer")

text_input = st.text_area("Enter text here:", height=300)

if st.button("Summarize"):
    if not text_input.strip():
        st.warning("enter text")
    else:
        try:
            summary = summarize_text(text_input)
            st.subheader("Summary")
            st.success(summary)
        except Exception as e:
            st.error(f"Error: {e}")
