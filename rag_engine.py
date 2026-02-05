import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBED_MODEL = "all-MiniLM-L6-v2"

def process_files(files, user_id):
    all_docs = []
    for f in files:
        ext = f.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(f.read())
            if ext == 'pdf':
                loader = PyPDFLoader(tmp.name)
            elif ext in ['docx', 'doc']:
                loader = Docx2txtLoader(tmp.name)
            all_docs.extend(loader.load())
            os.remove(tmp.name)
    
    if not all_docs: return

    splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(all_docs)
    Chroma.from_documents(
        splits, 
        HuggingFaceEmbeddings(model_name=EMBED_MODEL), 
        persist_directory=f"./chroma_db_{user_id}"
    )

def get_context(prompt, user_id):
    try:
        db = Chroma(persist_directory=f"./chroma_db_{user_id}", 
                    embedding_function=HuggingFaceEmbeddings(model_name=EMBED_MODEL))
        docs = db.similarity_search(prompt, k=3)
        return "\n".join([d.page_content for d in docs])
    except: return ""