# tag::llm[]
import streamlit as st
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(temperature=0, 
                    anthropic_api_key=st.secrets["ANTHROPIC_KEY"], 
                    model_name="claude-3-5-sonnet-20240620")
# end::llm[]

# tag::embedding[]
from langchain_community.embeddings import OllamaEmbeddings


embeddings = OllamaEmbeddings(model="all-minilm")
# end::embedding[]
