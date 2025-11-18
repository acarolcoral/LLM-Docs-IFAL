import json
from elasticsearch import Elasticsearch
from processador_ementas import processar_documento_para_ementa
from llama_cpp import Llama
import time

# Configurações
ES_URL = "http://localhost:9200"
INDEX = "documentos_ifal_llm"
MODEL_PATH = "models/gemma-3-gaia-pt-br-4b-it-q4_k_m.gguf"

def gerar_ementas_para_todos_documentos():
    """Gera ementas para todos os documentos e salva no Elasticsearch"""
    
    # Conectar ao Elasticsearch
    es = Elasticsearch(ES_URL)
    
    # Carregar modelo LLM
    print("🔄 Carregando modelo LLM...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=8192,
        n_threads=6,
        verbose=False
    )
    
    # Buscar TODOS os documentos
    print("📥 Buscando documentos...")
    resultado = es.search(
        index=INDEX,
        body={"size": 1000, "query": {"match_all": {}}}
    )
    
    documentos = resultado['hits']['hits']
    print(f"📄 Encontrados {len(documentos)} documentos")
    
    # Processar cada documento
    for i, doc in enumerate(documentos):
        doc_id = doc['_id']
        conteudo = doc['_source']['conteudo']
        arquivo = doc['_source']['arquivo']
        
        print(f"🔧 Processando {i+1}/{len(documentos)}: {arquivo}")
        
        try:
            # Gerar ementa
            ementa = processar_documento_para_ementa(conteudo, llm)
            
            # Atualizar documento no Elasticsearch com a ementa
            es.update(
                index=INDEX,
                id=doc_id,
                body={
                    "doc": {
                        "ementa": ementa,
                        "tem_ementa": True
                    }
                }
            )
            
            print(f"✅ Ementa gerada para {arquivo}")
            time.sleep(1)  # Evitar sobrecarga
            
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")
    
    print("🎉 Todas as ementas foram geradas e salvas!")

if __name__ == "__main__":
    gerar_ementas_para_todos_documentos()