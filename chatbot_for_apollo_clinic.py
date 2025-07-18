# -*- coding: utf-8 -*-
"""Chatbot for Apollo clinic.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Q-2Cxwmf9cbQ-fvXNIkJ5CMPLHGc1ho6

**Step 1 : Gather, load and Store the dataset**
"""

import json

with open("apollo_faq.json", "r", encoding="utf-8") as f:
    faq_list = json.load(f)



print((faq_list))

#"""Converting the Json file as Langchain compatible Document"""

from langchain.schema import Document

#converting the json into langchain compatible document object

docs = [Document(page_content=faq["answer"], metadata={"question":faq["question"]}) for faq in faq_list]

#spliiting long answers
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap=50)
splits = splitter.split_documents(docs)

#embedding them
from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name ='sentence-transformers/all-MiniLM-L6-v2')

# Storing the vectors in vector store, FAISS - Facebook AI similarity search - Makes it faster to get nearest vector
from langchain.vectorstores import FAISS

vector_store = FAISS.from_documents(documents=splits, embedding=embeddings)

#"""**Step 2: Define Prompt Template**"""

from langchain.prompts import PromptTemplate

template = """ You are a helpful assitant for a medical clinic.

Answer the following question using only the retrieved context.
if the answer is not in the context, say 'I don't have any information on that'

Context:
{context}

Question:
{question}

Answer:"""

prompt = PromptTemplate(template=template, input_variables=['context','question'])

#"""**STEP 3: LLM SETUP**"""

#!pip install -q llama-cpp-python langchain huggingface-hub
#!apt-get install -y git-lfs
#!git lfs install

#!git clone https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF

#!ls Mistral-7B-Instruct-v0.1-GGUF

#from langchain.llms import LlamaCpp

#llm = LlamaCpp(model_path="/content/Mistral-7B-Instruct-v0.1-GGUF/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
#               n_ctx=2048,
#               temperature = 0.3,
#               max_tokens = 512)


from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL")


llm = ChatOpenAI(
    openai_api_base=LLAMA_SERVER_URL,  # Strip off `/chat/completions`
    openai_api_key="not-needed",  # Dummy key, required by LangChain
    model_name="llama-3.2-1b-instruct-unsloth.gguf",  # Make sure this matches your server's model name
)

#"""**Step 4: Building LLM chain**"""

from langchain.chains import RetrievalQA

retriever = vector_store.as_retriever(search_type='similarity', k=3)

qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever, return_source_documents=True, chain_type_kwargs={"prompt":prompt})

#"""**Step 5: testing the code**"""

#query = "how to download my prescription"
#result = qa_chain(query)

#print("Answer:", result['result'])
#for doc in result['source_documents']:
#    print("\nSource:", doc.metadata["question"])

#queries = [
#    "What are your opening hours?",
#    "Do you offer international shipping?",
#    "Can I cancel my order after purchase?",
#    "Where is your returns policy?"
#]

#for q in queries:
#    result = qa_chain(q)
#    print(f"\nQ: {q}\nA: {result['result']}")


# ---- Streamlit UI ----
import streamlit as st

# ---- Streamlit Chat UI ----
st.title("💬 Welcome to the Clinic's Chatbot")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input
query = st.chat_input("Ask your question:")

if query:
    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": query})

    with st.spinner("Thinking..."):
        # Get response from your QA chain
        result = qa_chain(query)

        # Append bot response
        st.session_state.chat_history.append({"role": "assistant", "content": result['result'], "sources": result["source_documents"]})

# Display the chat
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(f"**Answer:** {msg['content']}")
            with st.expander("Source Documents"):
                for i, doc in enumerate(msg["sources"]):
                    st.markdown(f"**Source {i+1}**:\n{doc.page_content}")
