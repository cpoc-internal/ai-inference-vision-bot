import streamlit as st
import database as db
import rag_engine as rag
import llm_client as ai
import base64

# --- 1. INITIAL SETUP ---
st.set_page_config(page_title="Multimodal AI RAG", layout="wide")
db.init_db()

# --- 2. AUTHENTICATION UI ---
if "user_id" not in st.session_state:
    st.title("🔐 AI Multi-Tool Platform")
    
    # Restoring the Login/Register Tabs
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            user = db.login_user(u, p)
            if user:
                st.session_state.user_id, st.session_state.username = user
                # Start them off with a fresh session
                st.session_state.current_session_id = db.create_session(user[0])
                st.success(f"Welcome back, {user[1]}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
                
    with tab2:
        new_u = st.text_input("New Username", key="reg_user")
        new_p = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Create Account", use_container_width=True):
            if new_u and new_p:
                if db.create_user(new_u, new_p):
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Username already exists.")
            else:
                st.warning("Please fill in all fields.")
    st.stop() # Halt execution until user logs in

# --- 3. SIDEBAR: NAVIGATION & TOOLS ---
with st.sidebar:
    st.title(f"👤 {st.session_state.username}")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session_id = db.create_session(st.session_state.user_id)
        st.rerun()

    st.divider()
    
    # State management for auto-detaching widgets
    if "doc_key" not in st.session_state: st.session_state.doc_key = 0
    if "img_key" not in st.session_state: st.session_state.img_key = 0

    st.subheader("📁 Documents (PDF/Word)")
    docs = st.file_uploader("Add to Knowledge Base", type=["pdf", "docx"], accept_multiple_files=True, key=f"d_{st.session_state.doc_key}")
    if st.button("Process & Detach Docs", use_container_width=True):
        if docs:
            with st.spinner("Indexing files..."):
                rag.process_files(docs, st.session_state.user_id)
                st.session_state.doc_key += 1
                st.success("Documents added!")
                st.rerun()

    st.subheader("🖼️ Vision")
    img = st.file_uploader("Analyze Image", type=["jpg", "png", "jpeg"], key=f"i_{st.session_state.img_key}")
    if img:
        st.image(img, caption="Image Ready", use_container_width=True)

    st.divider()
    st.subheader("📜 Recent Chats")
    sessions = db.get_sessions(st.session_state.user_id)
    for s_id, title in sessions:
        # Highlight the current active session
        btn_label = f"💬 {title[:20]}"
        if st.button(btn_label, key=f"s_{s_id}", use_container_width=True):
            st.session_state.current_session_id = s_id
            st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 4. MAIN CHAT AREA ---
curr_id = st.session_state.get("current_session_id")

if curr_id:
    # Render main history
    history = db.get_history(curr_id)
    for role, text in history:
        with st.chat_message(role):
            st.markdown(text)
            if role == "assistant":
                with st.expander("📋 Copy Answer"):
                    st.code(text, language="markdown")

    # Chat Input
    if prompt := st.chat_input("Ask about your documents or the image..."):
        st.chat_message("user").markdown(prompt)
        
        # 1. Retrieval
        context = rag.get_context(prompt, st.session_state.user_id)
        
        # 2. Vision Encoding
        img_b64 = None
        if img:
            img_b64 = base64.b64encode(img.getvalue()).decode()
        
        # 3. AI Generation
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            try:
                # Update URL/Model if needed for your local vLLM Docker container
                stream = ai.get_vllm_response(prompt, context, img_b64, "http://localhost:8000/v1", "llava-hf/llava-1.5-7b-hf")
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
                
                # 4. Persistence
                db.save_message(curr_id, "user", prompt)
                db.save_message(curr_id, "assistant", full_res)
                
                # 5. Auto-Detach Image if used
                if img:
                    st.session_state.img_key += 1
                
                st.rerun() # Refresh to update sidebar titles and clear image
                
            except Exception as e:
                st.error(f"Connection Error: {e}. Check if vLLM is running.")
else:
    st.info("Start a new chat or select one from the sidebar to begin.")