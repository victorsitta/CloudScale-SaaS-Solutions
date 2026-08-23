import os
from pathlib import Path
from dotenv import load_dotenv

# Encontra a raiz do projeto (alura-challenge-agente-saas)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Carrega as variáveis de ambiente do arquivo .env (uso local)
load_dotenv(PROJECT_ROOT / ".env")

# No Streamlit Community Cloud não existe arquivo .env: as chaves são
# cadastradas em "Secrets" e expostas via st.secrets. Aqui elas são
# replicadas para os.environ para que o resto do código (que usa
# os.getenv) funcione igual em ambos os ambientes, sem duplicar lógica.
try:
    import streamlit as st
    for _key in list(st.secrets.keys()):
        os.environ.setdefault(_key, str(st.secrets[_key]))
except Exception:
    pass

# Provedor de LLM ativo: "groq" ou "cohere"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Configurações da Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Configurações da Cohere
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-a-03-2025")

# Senha para desbloquear ações administrativas na UI (trocar chave, reindexar, upload)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Configurações de Embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Diretórios
DATA_DIR = PROJECT_ROOT / "data"
FAISS_INDEX_DIR = PROJECT_ROOT / "faiss_index"
UPLOAD_DIR = PROJECT_ROOT / "data_uploaded"

# Garante que os diretórios existam
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Validação simples
def check_config():
    if LLM_PROVIDER == "cohere":
        if not COHERE_API_KEY:
            return False, "COHERE_API_KEY não configurada no arquivo .env."
    else:
        if not GROQ_API_KEY:
            return False, "GROQ_API_KEY não configurada no arquivo .env."
    return True, "Configuração carregada com sucesso!"
