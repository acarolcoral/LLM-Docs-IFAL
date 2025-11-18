import os
import pdfplumber
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# =====================================================
# ⚙️ CONFIGURAÇÕES INICIAIS
# =====================================================

# Nome do índice no Elasticsearch
INDEX = "documentos_ifal_llm"

# Conexão com o Elasticsearch local (sem autenticação e sem HTTPS)
es = Elasticsearch("http://localhost:9200")

# Teste rápido de conexão
try:
    info = es.info()
    print(f"🔗 Conectado ao Elasticsearch versão {info['version']['number']}")
except Exception as e:
    print("❌ Erro ao conectar ao Elasticsearch:", e)
    exit(1)

# Modelo para gerar embeddings semânticos dos textos
model = SentenceTransformer("all-MiniLM-L6-v2")

# Pasta onde estão os PDFs a serem indexados
PASTA_PDFS = "documentos/pdfs"  

# =====================================================
# 🧹 REINICIALIZAÇÃO DO ÍNDICE (APAGA E RECRIA)
# =====================================================

if es.indices.exists(index=INDEX):
    print(f"🧹 Apagando índice existente: {INDEX}")
    es.indices.delete(index=INDEX)

# Cria o índice com mapeamento para texto e embeddings
es.indices.create(
    index=INDEX,
    body={
        "mappings": {
            "properties": {
                "arquivo": {"type": "keyword"},
                "conteudo": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384,  # tamanho do embedding gerado pelo modelo
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
)

print(f"✅ Índice '{INDEX}' criado com sucesso.\n")

# =====================================================
# 📄 LEITURA E INDEXAÇÃO DOS PDFs (AGORA INTEIROS)
# =====================================================

pdfs_processados = 0

for arquivo in os.listdir(PASTA_PDFS):
    if arquivo.endswith(".pdf"):
        caminho = os.path.join(PASTA_PDFS, arquivo)
        print(f"📘 Lendo arquivo: {arquivo}")

        texto_total = ""

        # Extrai texto de cada página do PDF
        try:
            with pdfplumber.open(caminho) as pdf:
                for pagina_num, pagina in enumerate(pdf.pages, 1):
                    texto_pagina = pagina.extract_text() or ""
                    texto_total += texto_pagina + "\n"
                    print(f"   📄 Página {pagina_num}: {len(texto_pagina)} caracteres")
        except Exception as e:
            print(f"❌ Erro ao ler {arquivo}: {e}")
            continue

        if not texto_total.strip():
            print(f"⚠️ Nenhum texto encontrado em {arquivo}. Pulando arquivo.\n")
            continue

        # Remove espaços extras e quebras de linha múltiplas
        texto_total = " ".join(texto_total.split())
        
        print(f"   📊 Texto extraído: {len(texto_total)} caracteres")

        # Gera embedding do documento INTEIRO
        embedding = model.encode(texto_total).tolist()

        # Indexa o documento COMPLETO no Elasticsearch
        es.index(
            index=INDEX,
            document={
                "arquivo": arquivo,
                "conteudo": texto_total,
                "embedding": embedding
            }
        )

        pdfs_processados += 1
        print(f"✅ {arquivo} indexado como documento completo.\n")

print(f"🏁 Processamento concluído! {pdfs_processados} PDFs indexados como documentos completos.")