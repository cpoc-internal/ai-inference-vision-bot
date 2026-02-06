import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
import os

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



def extract_pdf_images(file_bytes, user_id, session_id):
    """Extracts images from PDF and returns a list of local paths."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    image_paths = []
    
    # Create directory for this session's images
    output_dir = f"./extracted_images/{user_id}/{session_id}"
    os.makedirs(output_dir, exist_ok=True)

    for page_index in range(len(doc)):
        for img_index, img in enumerate(doc.get_page_images(page_index)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            img_filename = f"pg{page_index}_img{img_index}.{ext}"
            img_path = os.path.join(output_dir, img_filename)
            
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            image_paths.append(img_path)
    return image_paths

def get_session_image_names(user_id, session_id):
    path = f"./extracted_images/{user_id}/{session_id}"
    if os.path.exists(path):
        return os.listdir(path)
    return []