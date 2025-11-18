import streamlit as st
from elasticsearch import Elasticsearch
import math
import os
from streamlit_pdf_viewer import pdf_viewer

# Configurações
INDEX = "documentos_ifal_llm"
ES_URL = "http://localhost:9200"
RESULTS_PER_PAGE = 10
PDF_BASE_PATH = "documentos/pdfs/"

# Título do app
st.set_page_config(page_title="Busca IFAL", layout="wide")
st.title("Documentos IFAL")
st.markdown("---")

# Inicializar session state
if 'resultados' not in st.session_state:
    st.session_state.resultados = []
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = 1
if 'doc_selecionado' not in st.session_state:
    st.session_state.doc_selecionado = None
if 'total_resultados' not in st.session_state:
    st.session_state.total_resultados = 0
if 'termo_busca' not in st.session_state:
    st.session_state.termo_busca = ""

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def conectar_elasticsearch():
    """Conecta ao Elasticsearch"""
    try:
        es = Elasticsearch(ES_URL)
        es.info()
        return es
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Elasticsearch: {e}")
        return None

def mostrar_pdf_com_viewer(nome_arquivo):
    """Exibe PDF com visualizador avançado"""
    caminho_pdf = os.path.join(PDF_BASE_PATH, nome_arquivo)
    
    if os.path.exists(caminho_pdf):
        st.success(f"✅ Carregando: {nome_arquivo}")
        
        # Visualizador com controles
        with st.container():
            pdf_viewer(input=caminho_pdf, width=700)
    else:
        st.error(f"❌ PDF não encontrado: {nome_arquivo}")
        st.info(f"💡 Verifique se o arquivo está em: {PDF_BASE_PATH}")

def extrair_nome_pdf(arquivo_nome):
    """Extrai nome do arquivo PDF do nome do documento"""
    if arquivo_nome.endswith('.pdf'):
        return arquivo_nome
    elif arquivo_nome.endswith('.txt'):
        return arquivo_nome.replace('.txt', '.pdf')
    else:
        return f"{arquivo_nome}.pdf"

def busca_unificada(termo, pagina=1, tamanho_pagina=10):
    """Busca unificada (full-text + semântica)"""
    if not es:
        return [], 0
    
    try:
        # Primeiro: busca textual (sempre funciona)
        query_textual = {
            "size": tamanho_pagina,
            "from": (pagina - 1) * tamanho_pagina,
            "query": {
                "multi_match": {
                    "query": termo,
                    "fields": ["conteudo", "arquivo", "ementa"],
                    "fuzziness": "AUTO"
                }
            },
            "_source": ["arquivo", "conteudo", "ementa", "tem_ementa"]
        }
        
        # Tenta busca semântica se disponível
        try:
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer("all-MiniLM-L6-v2")
            emb = embedder.encode(termo).tolist()
            
            # Query semântica separada
            query_semantica = {
                "size": tamanho_pagina,
                "from": (pagina - 1) * tamanho_pagina,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "knn_score",
                            "lang": "knn",
                            "params": {
                                "field": "embedding",
                                "query_value": emb,
                                "space_type": "cosinesimil"
                            }
                        }
                    }
                },
                "_source": ["arquivo", "conteudo", "ementa", "tem_ementa"]
            }
            
            # Executa ambas as buscas
            resultado_textual = es.search(index=INDEX, body=query_textual)
            resultado_semantica = es.search(index=INDEX, body=query_semantica)
            
            # Combina resultados (remove duplicatas)
            documentos_textual = resultado_textual['hits']['hits']
            documentos_semantica = resultado_semantica['hits']['hits']
            
            # Junta e remove duplicatas por _id
            todos_documentos = {}
            for doc in documentos_textual + documentos_semantica:
                todos_documentos[doc['_id']] = doc
            
            documentos = list(todos_documentos.values())
            total = len(documentos)
            
            return documentos, total
            
        except ImportError:
            # Fallback: apenas busca textual
            st.info("🔍 Buscando apenas por texto (semântica desativada)")
            resultado = es.search(index=INDEX, body=query_textual)
            total = resultado['hits']['total']['value']
            documentos = resultado['hits']['hits']
            return documentos, total
            
        except Exception as e_semantica:
            # Se houver erro na semântica, usa apenas textual
            st.warning(f"⚠️ Busca semântica temporariamente indisponível")
            resultado = es.search(index=INDEX, body=query_textual)
            total = resultado['hits']['total']['value']
            documentos = resultado['hits']['hits']
            return documentos, total
        
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return [], 0

# =============================================
# CONEXÃO ELASTICSEARCH
# =============================================

es = conectar_elasticsearch()

# =============================================
# INTERFACE DE BUSCA
# =============================================

with st.form("busca_form"):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        termo = st.text_input(
            " ", 
            placeholder="ex: edital, projeto, regulamento, seleção",
            value=st.session_state.termo_busca
        )
    
    with col2:
        st.write("")  # Espaçamento
        buscar = st.form_submit_button("🔍 Buscar")
    
    if buscar and termo.strip():
        with st.spinner("Buscando documentos..."):
            documentos, total = busca_unificada(termo, 1, RESULTS_PER_PAGE)
            st.session_state.resultados = documentos
            st.session_state.total_resultados = total
            st.session_state.pagina_atual = 1
            st.session_state.termo_busca = termo

# =============================================
# SEÇÃO DE PAGINAÇÃO
# =============================================

if st.session_state.resultados:
    total_paginas = math.ceil(st.session_state.total_resultados / RESULTS_PER_PAGE)
    inicio = (st.session_state.pagina_atual - 1) * RESULTS_PER_PAGE + 1
    fim = min(st.session_state.pagina_atual * RESULTS_PER_PAGE, st.session_state.total_resultados)
    
    st.markdown(f"**📊 Exibindo {inicio}-{fim} de {st.session_state.total_resultados} documentos encontrados**")
    
    # Controles de paginação
    if total_paginas > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ Primeira", disabled=st.session_state.pagina_atual == 1, use_container_width=True):
                st.session_state.pagina_atual = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ Anterior", disabled=st.session_state.pagina_atual == 1, use_container_width=True):
                st.session_state.pagina_atual -= 1
                st.rerun()
        
        with col3:
            st.markdown(f"**Página {st.session_state.pagina_atual} de {total_paginas}**", help="Navegue entre as páginas de resultados")
        
        with col4:
            if st.button("Próxima ▶️", disabled=st.session_state.pagina_atual == total_paginas, use_container_width=True):
                st.session_state.pagina_atual += 1
                st.rerun()
        
        with col5:
            if st.button("Última ⏭️", disabled=st.session_state.pagina_atual == total_paginas, use_container_width=True):
                st.session_state.pagina_atual = total_paginas
                st.rerun()

# =============================================
# LISTA DE RESULTADOS
# =============================================

if st.session_state.resultados:
    st.markdown("## 📄 Documentos Encontrados")
    
    # Buscar resultados da página atual
    documentos_pagina, _ = busca_unificada(
        st.session_state.termo_busca, 
        st.session_state.pagina_atual, 
        RESULTS_PER_PAGE
    )
    
    for i, doc in enumerate(documentos_pagina):
        arquivo = doc['_source']['arquivo']
        conteudo = doc['_source']['conteudo']
        ementa = doc['_source'].get('ementa', '')
        tem_ementa = doc['_source'].get('tem_ementa', False)
        
        # Card do documento
        with st.container():
            # Cabeçalho do documento
            st.markdown(f"### 📄 {arquivo}")
            
            # Ementa pré-gerada em collapse
            if tem_ementa and ementa:
                with st.expander("📋 **EMENTA**", expanded=False):
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #006633;'>
                    {ementa}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("⏳ Ementa em processamento...")
            
            # Preview do conteúdo
            #preview = conteudo[:500] + "..." if len(conteudo) > 500 else conteudo
            #st.write(preview)
            
            # Botão para ver documento completo
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                if st.button("📖 Ver Documento Completo", key=f"ver_{doc['_id']}", use_container_width=True):
                    st.session_state.doc_selecionado = doc
                    st.rerun()
            
            st.markdown("---")

# =============================================
# PÁGINA DO DOCUMENTO INDIVIDUAL
# =============================================

if st.session_state.doc_selecionado:
    doc = st.session_state.doc_selecionado
    arquivo = doc['_source']['arquivo']
    conteudo = doc['_source']['conteudo']
    ementa = doc['_source'].get('ementa', '')
    
    st.markdown("## 📖 Documento Completo")
    
    # Botão voltar
    if st.button("← Voltar para resultados"):
        st.session_state.doc_selecionado = None
        st.rerun()
    
    # Cabeçalho do documento
    st.markdown(f"### {arquivo}")
    st.markdown("**🏛️ Instituição:** IFAL - Instituto Federal de Alagoas")
    
    # Ementa pré-gerada
    if ementa:
        with st.expander("📋 **EMENTA**", expanded=True):
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #006633; margin: 10px 0;'>
            {ementa}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("ℹ️ Ementa não disponível para este documento")
    
    
    # Extrair nome do arquivo PDF
    nome_pdf = extrair_nome_pdf(arquivo)
    
    # Exibir PDF com visualizador avançado
    mostrar_pdf_com_viewer(nome_pdf)
   

# =============================================
# RODAPÉ
# =============================================

st.markdown("""
<div style='text-align: center; color: #666; padding-top: 200px;'>
<strong>Sistema de Busca de Documentos IFAL</strong><br>
Busca unificada: textual + semântica • Ementas 
</div>
""", unsafe_allow_html=True)