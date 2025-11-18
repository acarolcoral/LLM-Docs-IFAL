from elasticsearch import Elasticsearch

# Conectar ao Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Nome do índice
INDEX = "documentos_ifal_llm"

print("🔍 Testando conexão e dados...")

# Verificar se o índice existe
if es.indices.exists(index=INDEX):
    print("✅ Índice existe")
    
    # Contar documentos
    count = es.count(index=INDEX)['count']
    print(f"📊 Total de documentos no índice: {count}")
    
    # Buscar alguns documentos de exemplo
    result = es.search(index=INDEX, body={"size": 3, "query": {"match_all": {}}})
    
    print("\n📄 Primeiros documentos encontrados:")
    for hit in result['hits']['hits']:
        print(f"- ID: {hit['_id']}")
        print(f"  Arquivo: {hit['_source'].get('arquivo', 'N/A')}")
        print(f"  Conteúdo: {hit['_source'].get('conteudo', 'N/A')[:100]}...")
        print()
        
else:
    print("❌ Índice não existe. Execute primeiro o indexar_pdfs.py")