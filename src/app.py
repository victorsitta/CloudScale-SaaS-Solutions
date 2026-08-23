import os
import shutil
from pathlib import Path
import streamlit as st
from langchain_core.documents import Document

# Configuração robusta de importação
try:
    from src.document_loader import UniversalDocumentLoader
    from src.rag_engine import RAGEngine
    from src import config
except ImportError:
    from document_loader import UniversalDocumentLoader
    from rag_engine import RAGEngine
    import config

# Configuração da página Streamlit
st.set_page_config(
    page_title="CloudScale AI - Assistente RAG Corporativo",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para um visual corporativo premium
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --brand-navy: #0F172A;
        --brand-blue: #1E3A8A;
        --brand-blue-light: #3B82F6;
        --brand-accent: #06B6D4;
        --brand-bg: #F8FAFC;
        --brand-border: #E2E8F0;
        --brand-muted: #64748B;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Esconde o menu/rodapé padrão do Streamlit para um visual mais limpo */
    #MainMenu, footer { visibility: hidden; }

    /* Fundo geral da aplicação */
    .stApp {
        background: linear-gradient(180deg, #F1F5F9 0%, #F8FAFC 320px, #F8FAFC 100%);
        color: #0F172A;
    }

    /* Classes com cor própria que NUNCA devem ser resetadas pelas regras abaixo */
    /* .status-badge (+ .status-connected/.status-disconnected), .doc-item-ext, .hero-tag */

    /* Força texto escuro no conteúdo principal (fundo claro), independente do tema do
       sistema — escopado a `.main` para NÃO vazar para a sidebar (fundo escuro), e
       excluindo elementos com cor própria (badges/tags). */
    .stMain, .stMain .block-container,
    .stMain p:not(.status-badge), .stMain span:not(.status-badge):not(.hero-tag), .stMain li, .stMain label,
    .stMain div[data-testid="stMarkdownContainer"] p:not(.status-badge),
    .stMain div[data-testid="stMarkdownContainer"] span:not(.status-badge):not(.hero-tag),
    .stMain div[data-testid="stMarkdownContainer"] li,
    .stMain div[data-testid="stMarkdownContainer"] strong,
    .stMain div[data-testid="stMarkdownContainer"] em,
    .stMain div[data-testid="stExpander"] p,
    .stMain div[data-testid="stExpander"] span,
    .stMain div[data-testid="stExpander"] li,
    .stMain div[data-testid="stExpander"] summary,
    .stMain .element-container p, .stMain .element-container span {
        color: #0F172A !important;
    }

    /* Fundo branco explícito para área de chat */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF;
    }

    /* Sidebar com fundo escuro corporativo — todo texto claro por padrão,
       exceto elementos com cor própria (badges/ícones de extensão). */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1220 0%, #101B33 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    /* Fallback: texto claro por padrão na sidebar (baixa prioridade, sem !important) */
    section[data-testid="stSidebar"] * {
        color: #E2E8F0;
    }
    /* Reforça o fallback só onde algum componente do Streamlit tenta escurecer o
       texto, sem nunca tocar em elementos com cor própria (badges/tags) */
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p:not(.status-badge),
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] span:not(.status-badge):not(.doc-item-ext),
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] li,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] p,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] span,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
        color: #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] .stButton>button {
        background: linear-gradient(135deg, var(--brand-blue-light), var(--brand-accent));
        color: #ffffff;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
    }
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
        caret-color: #F8FAFC !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] .stTextInput input::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
    }

    /* Cabeçalho da barra lateral */
    .sidebar-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        color: #FFFFFF;
        font-size: 26px;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .sidebar-subtitle {
        font-size: 12.5px;
        color: #94A3B8;
        margin-bottom: 18px;
        font-weight: 500;
    }
    .sidebar-section-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #CBD5E1 !important;
        margin: 4px 0 10px 0;
    }

    /* Indicadores de status (badges) */
    .status-badge {
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.2px;
    }
    .status-badge::before {
        content: "";
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-connected,
    section[data-testid="stSidebar"] .status-connected {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399 !important;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .status-connected::before { background-color: #34D399; box-shadow: 0 0 6px #34D399; }
    .status-disconnected,
    section[data-testid="stSidebar"] .status-disconnected {
        background-color: rgba(239, 68, 68, 0.15);
        color: #F87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .status-disconnected::before { background-color: #F87171; }

    /* Document list item styling */
    .doc-item {
        font-size: 13px;
        padding: 8px 10px;
        background-color: rgba(255,255,255,0.05);
        border-radius: 8px;
        margin-bottom: 6px;
        border-left: 3px solid var(--brand-accent);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .doc-item-ext,
    section[data-testid="stSidebar"] .doc-item-ext {
        font-weight: 700;
        color: #93C5FD !important;
        background: rgba(59, 130, 246, 0.15);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 10.5px;
        letter-spacing: 0.5px;
    }

    /* Cabeçalho / hero da área principal */
    .hero-banner {
        background: linear-gradient(120deg, var(--brand-navy) 0%, var(--brand-blue) 55%, var(--brand-accent) 130%);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
    }
    /* Regra "à prova de balas": ID tem prioridade máxima no CSS, então TUDO
       dentro do banner é branco por padrão, não importa o que mais exista. */
    #cloudscale-hero, #cloudscale-hero * {
        color: #FFFFFF !important;
    }
    #cloudscale-hero .hero-title-sub {
        color: rgba(255,255,255,0.75) !important;
    }
    div.hero-title.hero-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 30px;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
        margin: 0 0 6px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    div.hero-title.hero-title span.hero-title-sub.hero-title-sub {
        color: rgba(255,255,255,0.7) !important;
        font-weight: 600;
        font-size: 20px;
    }
    p.hero-subtitle.hero-subtitle {
        color: rgba(255,255,255,0.9) !important;
        font-size: 14.5px;
        line-height: 1.6;
        max-width: 780px;
        margin: 0;
    }
    p.hero-subtitle.hero-subtitle strong.hero-strong.hero-strong {
        color: #FFFFFF !important;
    }
    .hero-tags {
        margin-top: 14px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .hero-tag {
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.25);
        color: #FFFFFF !important;
        font-size: 11.5px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 999px;
    }

    /* Fonte da resposta da IA */
    .source-card {
        background-color: #FFFFFF;
        border: 1px solid var(--brand-border);
        border-left: 3px solid var(--brand-blue-light);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #334155 !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .source-meta {
        font-weight: 700;
        color: var(--brand-blue);
        margin-bottom: 6px;
        font-size: 12.5px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .source-content {
        color: #475569;
        line-height: 1.55;
    }

    /* Chat */
    div[data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 4px 2px;
    }
    /* Mantém o fundo original da caixa de chat, só garante que a letra
       digitada fique branca e legível (o fundo é escuro). */
    .stChatInput textarea {
        border-radius: 12px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
    }
    .stChatInput textarea::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }
    div[data-testid="stChatInput"] * {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# Ícones por extensão de arquivo (para uma UI mais rica)
FILE_ICONS = {
    "PDF": "📕", "DOCX": "📘", "XLSX": "📗", "CSV": "📊",
    "PPTX": "📙", "MD": "📝", "JSON": "🧩", "HTML": "🌐",
}

# 1. Gerenciamento do Estado da API Key no Session State
PROVIDER_NAME = "Cohere" if config.LLM_PROVIDER == "cohere" else "Groq"
PROVIDER_ENV_VAR = "COHERE_API_KEY" if config.LLM_PROVIDER == "cohere" else "GROQ_API_KEY"
PROVIDER_DEFAULT_KEY = config.COHERE_API_KEY if config.LLM_PROVIDER == "cohere" else config.GROQ_API_KEY
PROVIDER_MODEL = config.COHERE_MODEL if config.LLM_PROVIDER == "cohere" else config.GROQ_MODEL

if "api_key" not in st.session_state:
    st.session_state.api_key = PROVIDER_DEFAULT_KEY

# Se a chave da API foi inserida na barra lateral, atualiza o ambiente
if st.session_state.api_key:
    os.environ[PROVIDER_ENV_VAR] = st.session_state.api_key

# 2. Inicialização do RAG Engine (Singleton no session state)
@st.cache_resource(show_spinner=False)
def get_rag_engine():
    return RAGEngine()

# Tenta carregar o motor RAG. Se houver algum erro por conta de pacotes, exibe uma mensagem
try:
    rag_engine = get_rag_engine()
except Exception as e:
    st.error(f"Erro ao inicializar o motor de inteligência RAG: {e}")
    rag_engine = None

# Primeira execução em um ambiente novo (ex: Streamlit Community Cloud): o
# faiss_index/ não é versionado no Git, então a base é indexada automaticamente
# a partir dos documentos oficiais em data/, sem exigir desbloqueio administrativo.
if rag_engine and rag_engine.vector_store is None and config.DATA_DIR.exists() and any(config.DATA_DIR.iterdir()):
    with st.spinner("Primeira execução: indexando a base de conhecimento oficial..."):
        initial_docs = UniversalDocumentLoader.load_directory(config.DATA_DIR)
        if initial_docs:
            rag_engine.initialize_vector_store(initial_docs)

# 3. Funções Auxiliares
def get_all_indexed_files():
    """Recupera a lista de todos os arquivos indexados das pastas data/ e data_uploaded/"""
    files = []
    # Pasta corporativa oficial
    if config.DATA_DIR.exists():
        for f in config.DATA_DIR.iterdir():
            if f.is_file() and not f.name.startswith(".") and not f.name.startswith("~$"):
                files.append((f, "Oficial"))
    # Pasta de uploads
    if config.UPLOAD_DIR.exists():
        for f in config.UPLOAD_DIR.iterdir():
            if f.is_file() and not f.name.startswith(".") and not f.name.startswith("~$"):
                files.append((f, "Enviado"))
    return files

def trigger_reindex():
    """Limpa e reindexa toda a base de dados."""
    if not rag_engine:
        st.error("RAG Engine não inicializado.")
        return
        
    with st.spinner("Reindexando base de dados corporativa... Isso pode levar um minuto."):
        # Carrega dados oficiais
        docs = UniversalDocumentLoader.load_directory(config.DATA_DIR)
        
        # Carrega dados de upload (se houver)
        if config.UPLOAD_DIR.exists():
            uploaded_docs = UniversalDocumentLoader.load_directory(config.UPLOAD_DIR)
            docs.extend(uploaded_docs)
            
        if docs:
            success = rag_engine.initialize_vector_store(docs)
            if success:
                st.toast("Base de conhecimento reindexada com sucesso!", icon="✨")
                st.rerun()
            else:
                st.error("Erro ao reconstruir o banco de vetores.")
        else:
            st.warning("Nenhum documento encontrado para indexação.")

if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False

def render_sources(sources_data):
    """Renderiza os cards de fontes consultadas dentro de um expander padronizado."""
    with st.expander(f"📌 Fontes Consultadas ({len(sources_data)})"):
        for src in sources_data:
            ext = str(src["file_type"]).upper().lstrip(".")
            icon = FILE_ICONS.get(ext, "📄")
            st.markdown(
                f'<div class="source-card">'
                f'<div class="source-meta">{icon} {src["file_name"]} <span style="color:#94A3B8; font-weight:500;">· {ext}</span></div>'
                f'<div class="source-content">{src["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

# 4. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    # Logo e Branding
    st.markdown('<div class="sidebar-header">☁️ CloudScale AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Assistente Inteligente de Conhecimento Corporativo</div>', unsafe_allow_html=True)
    st.divider()

    # Área administrativa protegida por senha: trocar chave, reindexar e enviar
    # documentos ficam visíveis (para fins de demonstração), mas só funcionam
    # depois de desbloqueadas — evita que qualquer usuário do app altere a base.
    if st.session_state.admin_unlocked:
        st.markdown('<span class="status-badge status-connected">🔓 Modo Administrador Ativo</span>', unsafe_allow_html=True)
        if st.button("Bloquear novamente", use_container_width=True):
            st.session_state.admin_unlocked = False
            st.rerun()
    else:
        with st.expander("🔒 Área Administrativa (requer senha)"):
            admin_pwd = st.text_input("Senha de administrador:", type="password", key="admin_pwd_input")
            if st.button("Desbloquear", use_container_width=True):
                if config.ADMIN_PASSWORD and admin_pwd == config.ADMIN_PASSWORD:
                    st.session_state.admin_unlocked = True
                    st.toast("Ações administrativas desbloqueadas!", icon="🔓")
                    st.rerun()
                else:
                    st.error("Senha incorreta.")

    st.divider()

    st.markdown('<div class="sidebar-section-label">Conexão com o Modelo</div>', unsafe_allow_html=True)
    # Status da API do provedor de LLM ativo e Input se necessário
    if not st.session_state.api_key:
        st.markdown(f'<span class="status-badge status-disconnected">API {PROVIDER_NAME}: Desconectada</span>', unsafe_allow_html=True)
        user_key = st.text_input(f"Insira sua {PROVIDER_NAME} API Key:", type="password", key="llm_key_input")
        if user_key:
            st.session_state.api_key = user_key
            os.environ[PROVIDER_ENV_VAR] = user_key
            st.toast("Chave de API registrada!", icon="🔑")
            st.rerun()
    else:
        st.markdown(f'<span class="status-badge status-connected">API {PROVIDER_NAME}: Conectada</span>', unsafe_allow_html=True)
        # Mostrar o modelo ativo
        st.caption(f"Modelo: `{PROVIDER_MODEL}`")
        if st.button(
            "🔒 Alterar Chave de API" if not st.session_state.admin_unlocked else "Alterar Chave de API",
            disabled=not st.session_state.admin_unlocked,
            help=None if st.session_state.admin_unlocked else "Desbloqueie a Área Administrativa para alterar a chave.",
        ):
            st.session_state.api_key = ""
            os.environ[PROVIDER_ENV_VAR] = ""
            st.rerun()
            
    st.divider()

    st.markdown('<div class="sidebar-section-label">Base de Conhecimento</div>', unsafe_allow_html=True)
    # Indicadores da Base de Conhecimento
    indexed_files = get_all_indexed_files()
    num_files = len(indexed_files)

    # Exibe badge de status da Base Vetorial
    if rag_engine and rag_engine.vector_store is not None:
        st.markdown('<span class="status-badge status-connected">Base Vetorial: Pronta</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">Base Vetorial: Vazia / Não Indexada</span>', unsafe_allow_html=True)

    st.markdown(f"**Documentos carregados:** {num_files}")

    # Botão de reindexação rápida (protegido por senha de administrador)
    if st.button(
        "🔄 Regenerar / Reindexar Base de Dados" if st.session_state.admin_unlocked else "🔒 Regenerar / Reindexar Base de Dados",
        use_container_width=True,
        disabled=not st.session_state.admin_unlocked,
        help=None if st.session_state.admin_unlocked else "Desbloqueie a Área Administrativa para reindexar.",
    ):
        trigger_reindex()

    st.divider()

    # Upload de novos arquivos em tempo real (protegido por senha de administrador)
    st.markdown('<div class="sidebar-section-label">Adicionar Documento</div>', unsafe_allow_html=True)
    if not st.session_state.admin_unlocked:
        st.caption("🔒 Desbloqueie a Área Administrativa para enviar documentos.")
    uploaded_file = st.file_uploader(
        "Selecione um arquivo:",
        type=["pdf", "docx", "xlsx", "csv", "pptx", "md", "json", "html"],
        label_visibility="collapsed",
        disabled=not st.session_state.admin_unlocked,
    )

    if uploaded_file is not None and st.session_state.admin_unlocked:
        # Salva o arquivo na pasta de uploads
        upload_path = config.UPLOAD_DIR / uploaded_file.name
        
        with st.spinner(f"Processando {uploaded_file.name}..."):
            # Escreve o arquivo fisicamente
            with open(upload_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            try:
                # Carrega o documento usando UniversalLoader
                new_docs = UniversalDocumentLoader.load_file(upload_path)
                
                # Adiciona ao FAISS
                if rag_engine:
                    success = rag_engine.add_documents_to_store(new_docs)
                    if success:
                        st.toast(f"{uploaded_file.name} indexado com sucesso!", icon="✅")
                        st.rerun()
                    else:
                        st.error("Erro ao adicionar documento no banco de vetores.")
                else:
                    st.error("RAG Engine não está disponível.")
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                if upload_path.exists():
                    upload_path.unlink() # remove se falhar
                    
    st.divider()

    # Lista detalhada dos documentos ativos
    st.markdown('<div class="sidebar-section-label">Documentos na Base</div>', unsafe_allow_html=True)
    if indexed_files:
        for file_path, origin in indexed_files:
            ext = file_path.suffix.upper()[1:]
            origin_badge = "🏢" if origin == "Oficial" else "👤"
            file_icon = FILE_ICONS.get(ext, "📄")
            st.markdown(
                f'<div class="doc-item">'
                f'<span>{file_icon} {origin_badge} {file_path.name}</span>'
                f'<span class="doc-item-ext">{ext}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Nenhum arquivo na pasta de dados corporativos.")

# 5. PAINEL PRINCIPAL (CHAT)
st.markdown(f"""
<div class="hero-banner" id="cloudscale-hero">
    <div class="hero-title">☁️ CloudScale AI <span class="hero-title-sub">/ Assistente Corporativo</span></div>
    <p class="hero-subtitle">
        Olá! Sou o <strong class="hero-strong">CloudScale Bot</strong>, o assistente oficial da <strong class="hero-strong">CloudScale SaaS Solutions</strong>.
        Estou aqui para esclarecer dúvidas sobre nossos manuais, planos de preços, FAQs de suporte,
        políticas de segurança (LGPD) e APIs de integração — sempre com base nos documentos internos.
    </p>
    <div class="hero-tags">
        <span class="hero-tag">🔎 Busca por Similaridade</span>
        <span class="hero-tag">📚 8+ Formatos de Documento</span>
        <span class="hero-tag">🤖 {PROVIDER_NAME} · {PROVIDER_MODEL}</span>
        <span class="hero-tag">🔐 Respostas Fundamentadas em Fontes</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Inicialização do histórico de mensagens no session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens antigas do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Se houver fontes salvas na mensagem do histórico, reconstrói o expander de fontes
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            render_sources(message["sources"])

# Input de mensagens do colaborador
if user_query := st.chat_input("Pergunte algo sobre os documentos da CloudScale SaaS..."):
    # Adiciona a mensagem do usuário ao chat e ao histórico
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
        
    # Gera a resposta com o RAG
    with st.chat_message("assistant"):
        if not st.session_state.api_key:
            error_msg = f"Chave da API {PROVIDER_NAME} ausente. Por favor, adicione sua API Key na barra lateral para conversar."
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        elif not rag_engine or rag_engine.vector_store is None:
            error_msg = "O banco de dados de conhecimento está vazio. Clique em **Regenerar / Reindexar Base de Dados** na barra lateral para indexar os documentos iniciais."
            st.warning(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            # Spinner de carregamento do processamento do LLM
            with st.spinner("Pesquisando base interna e elaborando resposta..."):
                response, source_docs = rag_engine.query(user_query)
                
            # Exibe a resposta
            st.markdown(response)
            
            # Formata metadados das fontes para armazenar no histórico do chat
            sources_data = []
            for doc in source_docs:
                sources_data.append({
                    "file_name": doc.metadata.get("file_name", "Desconhecido"),
                    "file_type": doc.metadata.get("file_type", "Desconhecido"),
                    "content": doc.page_content
                })
                
            # Se houver documentos fontes, exibe o expander com os trechos e metadados
            if sources_data:
                render_sources(sources_data)
            
            # Salva a resposta e fontes no histórico
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": sources_data
            })
