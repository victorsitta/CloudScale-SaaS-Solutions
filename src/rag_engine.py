import os
from pathlib import Path
from typing import List, Tuple, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_cohere import ChatCohere
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Importa caminhos configurados de forma robusta
try:
    from src.config import (
        LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL,
        COHERE_API_KEY, COHERE_MODEL,
        EMBEDDING_MODEL, FAISS_INDEX_DIR,
    )
except ImportError:
    from config import (
        LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL,
        COHERE_API_KEY, COHERE_MODEL,
        EMBEDDING_MODEL, FAISS_INDEX_DIR,
    )

class RAGEngine:
    """
    Motor RAG para o assistente CloudScale Bot.
    Gerencia chunking, embeddings, indexação vetorial com FAISS e integração com a Groq.
    """
    
    def __init__(self):
        # Configuração do divisor de texto (chunking)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150
        )
        
        # Inicialização do modelo de embeddings local
        # O sentence-transformers/all-MiniLM-L6-v2 roda 100% local no CPU
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        
        self.vector_store: Optional[FAISS] = None
        self._load_existing_store()
        
    def _load_existing_store(self):
        """Tenta carregar um banco de vetores FAISS persistido localmente."""
        if FAISS_INDEX_DIR.exists() and (FAISS_INDEX_DIR / "index.faiss").exists():
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=str(FAISS_INDEX_DIR),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"[OK] Banco de vetores FAISS carregado de: {FAISS_INDEX_DIR.resolve()}")
            except Exception as e:
                print(f"[AVISO] Erro ao carregar o banco de vetores local: {e}. Um novo banco será criado.")
                self.vector_store = None
        else:
            self.vector_store = None

    def initialize_vector_store(self, documents: List[Document]) -> bool:
        """
        Recebe uma lista de Documents, divide-os em chunks,
        gera os embeddings e inicializa/salva o banco de vetores FAISS.
        """
        if not documents:
            print("[AVISO] Nenhum documento fornecido para indexacao.")
            return False
            
        print(f"[INFO] Dividindo {len(documents)} documentos em pedacos...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"[INFO] Total de chunks gerados: {len(chunks)}")
        
        print("[INFO] Gerando embeddings e inserindo no FAISS...")
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Salva localmente
        FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(FAISS_INDEX_DIR))
        print(f"[OK] Banco de vetores FAISS salvo em: {FAISS_INDEX_DIR.resolve()}")
        return True

    def add_documents_to_store(self, documents: List[Document]) -> bool:
        """Adiciona novos documentos ao banco de vetores FAISS existente e salva no disco."""
        if not documents:
            return False
            
        print(f"[INFO] Dividindo {len(documents)} novos documentos em pedacos...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"[INFO] Total de novos chunks gerados: {len(chunks)}")
        
        if not self.vector_store:
            # Se não houver vector store ainda, inicializa um novo
            return self.initialize_vector_store(documents)
            
        print("[INFO] Adicionando embeddings ao FAISS existente...")
        self.vector_store.add_documents(chunks)
        
        # Salva localmente
        FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(FAISS_INDEX_DIR))
        print(f"[OK] Banco de vetores FAISS atualizado e salvo em: {FAISS_INDEX_DIR.resolve()}")
        return True


    def get_retriever(self, search_kwargs: dict = None):
        """Retorna o retriever do FAISS para busca de similaridade."""
        if not self.vector_store:
            self._load_existing_store()
            
        if not self.vector_store:
            raise ValueError("Banco de vetores não inicializado. Carregue documentos primeiro.")
            
        kwargs = search_kwargs or {"k": 4}
        return self.vector_store.as_retriever(search_kwargs=kwargs)

    def query(self, question: str) -> Tuple[str, List[Document]]:
        """
        Executa a busca de similaridade no FAISS e chama o LLM da Groq
        com o template de prompt exigido pelas regras de conduta.
        """
        # 1. Recupera os documentos relevantes
        try:
            retriever = self.get_retriever()
            retrieved_docs = retriever.invoke(question)
        except Exception as e:
            # Caso o banco não esteja carregado
            return f"Desculpe, a base de conhecimento não está indexada. Detalhe: {e}", []
            
        # 2. Formata o contexto
        context_parts = []
        for doc in retrieved_docs:
            source_name = doc.metadata.get("file_name", "Documento desconhecido")
            context_parts.append(f"[Fonte: {source_name}]\n{doc.page_content}")
            
        context_text = "\n\n".join(context_parts)
        
        # 3. Define o prompt exigido pelo edital
        prompt_template = PromptTemplate.from_template(
            "Você é o CloudScale Bot, o assistente virtual corporativo da CloudScale SaaS Solutions.\n"
            "Sua função é responder às dúvidas dos colaboradores de forma clara, profissional e objetiva, "
            "baseando-se EXCLUSIVAMENTE no contexto fornecido abaixo.\n\n"
            "REGRAS DE CONDUTA:\n"
            "1. Responda apenas com base nas informações do CONTEXTO.\n"
            "2. Se a informação não estiver presente no contexto, diga educadamente: "
            "\"Desculpe, não encontrei essa informação nos documentos internos da CloudScale SaaS.\"\n"
            "3. Mencione sempre o nome do documento fonte onde encontrou a resposta.\n\n"
            "CONTEXTO RELEVANTE:\n"
            "{context}\n\n"
            "PERGUNTA DO COLABORADOR:\n"
            "{question}\n\n"
            "RESPOSTA RECOMENDADA:"
        )
        
        # 4. Conecta com o provedor de LLM configurado (Groq ou Cohere)
        provider = LLM_PROVIDER
        if provider == "cohere":
            if not COHERE_API_KEY:
                return "Erro: COHERE_API_KEY não configurada no ambiente. Adicione sua chave no arquivo .env da aplicação.", []
        else:
            if not GROQ_API_KEY:
                return "Erro: GROQ_API_KEY não configurada no ambiente. Adicione sua chave no arquivo .env da aplicação.", []

        try:
            if provider == "cohere":
                llm = ChatCohere(
                    cohere_api_key=COHERE_API_KEY,
                    model=COHERE_MODEL,
                    temperature=0.1
                )
            else:
                llm = ChatGroq(
                    groq_api_key=GROQ_API_KEY,
                    model_name=GROQ_MODEL,
                    temperature=0.1
                )

            chain = prompt_template | llm | StrOutputParser()

            # 5. Executa a cadeia
            response = chain.invoke({
                "context": context_text,
                "question": question
            })

            return response, retrieved_docs

        except Exception as e:
            return f"Ocorreu um erro ao consultar o modelo {provider.upper()}: {str(e)}", retrieved_docs
