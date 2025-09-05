from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from typing import List, TypedDict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import tiktoken

load_dotenv()

token_max = 1000
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.5)

prompt_template = PromptTemplate.from_template("""
You are a helpful assistant. Rewrite the following document for better understanding without losing much content: 

{text}

Summary:
""")

prompt_template1 = PromptTemplate.from_template("""
You are a helpful assistant. Summarize the following document:

{text}

Summary:
""")
finalize_chain= prompt_template | llm
summary_chain= prompt_template1 | llm


class State(TypedDict):
    text: str
    docs: List[Document]

def count_tokens(text):
    tokens= llm.get_num_tokens(text)
    return tokens

def check(state):
    return state

def route_check(state):
    token_count = count_tokens(state["text"])
    print("Token count:", token_count)
    return "summarize" if token_count <= token_max else "split"


def summarize(state):
    result = finalize_chain.invoke({"text": state["text"]})
    
    return {"text": result.content, "docs": []}


def split_text(state):
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=token_max,
        chunk_overlap=0
    )
    docs = splitter.create_documents([state["text"]])

    for i, doc in enumerate(docs):
        tokens = count_tokens(doc.page_content)
        print(f"Chunk {i+1}: {tokens} tokens")
    return {"text": state["text"], "docs": docs}


def summarize_chunks(state):
    summaries = []
    for doc in state["docs"]:
        result = summary_chain.invoke({"text": doc.page_content})
        result_text = result.content 
        
        summaries.append(Document(page_content=result_text))
    return {"text": "", "docs": summaries}



def merge_summaries(state):
    merged_text = "\n".join(doc.page_content for doc in state["docs"])
    return {"text": merged_text, "docs": state["docs"]}

# graph
graph = StateGraph(State)
graph.add_node("check", check)
graph.add_node("summarize", summarize)
graph.add_node("split", split_text)
graph.add_node("summarize_chunks", summarize_chunks)
graph.add_node("merge", merge_summaries)

graph.set_entry_point("check")
graph.add_conditional_edges("check", route_check, {
    "summarize": "summarize",
    "split": "split"
})
graph.add_edge("split", "summarize_chunks")
graph.add_edge("summarize_chunks", "merge")
graph.add_edge("merge", "check")
graph.add_edge("summarize", END)

app = graph.compile()

def summarize_text(text):
    result = app.invoke({"text": text, "docs": []})
    return result["text"]



# from IPython.display import Image

# Image(app.get_graph().draw_mermaid_png())

# with open("graph.png", "wb") as f:
#     f.write(app.get_graph().draw_mermaid_png())

