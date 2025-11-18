from elasticsearch import Elasticsearch
import streamlit as st

# Configurações
INDEX = "documentos_ifal_llm"
ES_URL = "http://localhost:9200"

print("=== DIAGNÓSTICO DO SISTEMA ===")

# Testar conexão com Elasticsearch
try:
    es = Elasticsearch(ES_URL)
    info = es.info()
    print(f"✅ Elasticsearch conectado - Versão: {info['version']['number']}")
except Exception as e:
    print(f"❌ Falha na conexão com Elasticsearch: {e}")
    exit(1)

# Verificar se o índice existe
if es.indices.exists(index=INDEX):
    print(f"✅ Índice '{INDEX}' existe")
    
    # Contar documentos
    count_result = es.count(index=INDEX)
    total_docs = count_result['count']
    print(f"📊 Total de documentos: {total_docs}")
    
    # Buscar todos os documentos
    if total_docs > 0:
        result = es.search(index=INDEX, body={"query": {"match_all": {}}, "size": 10})
        print("\n📄 Documentos encontrados:")
        for i, hit in enumerate(result['hits']['hits']):
            print(f"{i+1}. ID: {hit['_id']}")
            print(f"   Arquivo: {hit['_source'].get('arquivo', 'NÃO ENCONTRADO')}")
            conteudo = hit['_source'].get('conteudo', '')
            print(f"   Conteúdo: {len(conteudo)} caracteres")
            print(f"   Preview: {conteudo[:100]}...")
            print()
    else:
        print("❌ Índice existe mas está vazio!")
        
else:
    print(f"❌ Índice '{INDEX}' não existe!")