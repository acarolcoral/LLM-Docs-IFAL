import os
from huggingface_hub import hf_hub_download

# Pasta destino
DESTINO = "models"
os.makedirs(DESTINO, exist_ok=True)

# Lista de modelos GGUF que queremos baixar
modelos = [
    #{
    #    "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    #    "arquivo": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    #},
   # {
   #     "repo": "TheBloke/phi-2-GGUF",
    #    "arquivo": "phi-2.Q4_K_M.gguf"
   # }, 
    {
       "repo": "cnmoro/Gemma-3-Gaia-PT-BR-4b-it-Q4_K_M-GGUF",
        "arquivo": "gemma-3-gaia-pt-br-4b-it-q4_k_m.gguf"
    }
]

for m in modelos:
    print(f"⬇️ Baixando {m['arquivo']} de {m['repo']}...")
    caminho = hf_hub_download(
        repo_id=m["repo"],
        filename=m["arquivo"],
        local_dir=DESTINO
    )
    print(f"✅ Salvo em {caminho}")

print("\n🎉 Todos os modelos foram baixados para a pasta 'models/'!")
