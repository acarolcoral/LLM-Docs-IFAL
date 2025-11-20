# LLM DOCS IFAL 


## Plataforma de teste para integração de LLMs ao projeto [Documentos IFAL](https://github.com/thiagok2/documentos-ifal "Repositório do projeto")


## Passo a passo para instalação das dependências:

## 1. Crie um ambiente virtual 

### Para o Linux

#### Instalar:

    sudo apt install python3.12-venv

    sudo python3 -m venv venv

#### Ativação:

    source venv/bin/activate 

### Para o Windows

#### Instalar:

    python -m venv venv

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

#### Ativação:

    venv\Scripts\activate



## 2. Instalando compilador C++
Alguns pacotes ultilizados pelo projeto -  em especial o llama-cpp-python - necessitam de um compilador C/C++ para sua execução.
Caso a sua máquina já possua esse requisito pule essa etapa.
### Para o Linux:

    sudo apt update
    sudo apt install build-essential

### Para o Windows:

Instalar o [VisualStudio C/C++](https://visualstudio.microsoft.com/pt-br/vs/features/cplusplus/ "Link para baixar")



## 3. Instale as dependências

    pip install -r requirements.txt



## 4. Rodar o Elastic  

### Linux:

    docker run --name elasticsearch \
    -p 9200:9200 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    -e "xpack.security.http.ssl.enabled=false" \
    docker.elastic.co/elasticsearch/elasticsearch:8.11.0

### Windows:

    docker run --name elasticsearch_llm `
    -p 9200:9200 `
    -e "discovery.type=single-node" `
    -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" `
    docker.elastic.co/elasticsearch/elasticsearch:8.11.0

## 5. Baixar os modelos de LLM

- Presisa estar com o venv ativado

### Linux:

    python3 baixar_modelos.py

### Windows:

    python baixar_modelos.py


## 6. Indexar os documentos

### Linux: 

    python3 indexar_pdfs.py

### Windows: 

    python indexar_pdfs.py


## 7. Gerar as ementas

### Linux: 

    python3 gerar_ementas.py

### Windows: 

    python gerar_ementas.py


## 8. Rodar a aplicação

    streamlit run app.py



