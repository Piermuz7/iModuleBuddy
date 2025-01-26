import streamlit as st
from llama_index.llms.anthropic import Anthropic

llm = Anthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=st.secrets["ANTHROPIC_KEY"],
    max_tokens=8192,
)

# TODO: Migrate emebedding implementation to llama-index
from langchain_community.embeddings import OllamaEmbeddings

# Configuration instructions:
#   1: Install ollama locally
#   2: Run from the command line: ollama pull mxbai-embed-large
#   3: Run from the command line: ollama serve
embeddings = OllamaEmbeddings(
    model="mxbai-embed-large",
)
# end::embedding[]
