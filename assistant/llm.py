import streamlit as st
from llama_index.llms.anthropic import Anthropic

llm = Anthropic(
    model="claude-3-7-sonnet-20250219",
    api_key=st.secrets["ANTHROPIC_KEY"],
    temperature=0,
    max_tokens=64000,
)

# TODO: Migrate emebedding implementation to llama-index
from langchain_ollama import OllamaEmbeddings

# Configuration instructions:
#   1: Install ollama locally
#   2: Run from the command line: ollama pull mxbai-embed-large
#   3: Run from the command line: ollama serve
embeddings = OllamaEmbeddings(
    model="mxbai-embed-large",
)
# end::embedding[]
