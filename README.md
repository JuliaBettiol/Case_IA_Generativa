# Panvel AI Assistant

Assistente conversacional de IA Generativa desenvolvido para o desafio técnico do Grupo Panvel.

A aplicação possui dois fluxos principais:

- **RAG sobre bulas de medicamentos**, com recuperação semântica e indicação das fontes utilizadas.
- **Tool Calling para consultas de filiais**, utilizando os dados estruturados disponibilizados no desafio.

O sistema também possui contexto multi-turn, streaming de respostas, guardrails para consultas farmacológicas e observabilidade das execuções.

---

## Tecnologias

### Backend

- Python
- FastAPI
- OpenAI
- Qdrant
- Pandas
- Pydantic
- Pytest

### Frontend

- React
- TypeScript
- Vite
- Nginx

### Infraestrutura

- Docker
- Docker Compose

---

# Como executar

A forma recomendada de executar o projeto é através do Docker Compose.

## 1. Pré-requisitos

É necessário ter instalado:

- Git
- Docker
- Docker Compose

Também é necessária uma chave de API válida da OpenAI.

---

## 2. Clone o repositório

```bash
git clone https://github.com/JuliaBettiol/Case_IA_Generativa.git
cd Case_IA_Generativa
```

---

## 3. Configure as variáveis de ambiente

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Abra o arquivo `.env` e informe sua chave da OpenAI:

```env
OPENAI_API_KEY=sua_chave_openai
```

As demais configurações já possuem valores padrão adequados para execução local.

> O arquivo `.env` não é versionado pelo Git.

---

## 4. Execute a aplicação

Na raiz do projeto:

```bash
docker compose up --build
```

Na primeira execução, o projeto irá:

1. iniciar o Qdrant;
2. processar as 20 bulas disponibilizadas no desafio;
3. gerar os embeddings;
4. criar o índice vetorial;
5. iniciar o backend;
6. iniciar o frontend.

A primeira inicialização pode levar um pouco mais de tempo devido à geração dos embeddings.

Nas próximas execuções, o índice persistido é reutilizado quando já estiver completo.

---

## 5. Acesse a aplicação

Após a inicialização:

### Frontend

```text
http://localhost:5173
```

### Backend

```text
http://localhost:8000/docs
```

### Qdrant

```text
http://localhost:6333
```

---

# Como testar o assistente

## Consulta de bula — RAG

Experimente:

```text
Quais são os efeitos adversos do Rohydorm?
```

O sistema deve:

- identificar que a pergunta é sobre uma bula;
- recuperar os trechos relevantes no Qdrant;
- gerar a resposta com base no contexto recuperado;
- apresentar a bula utilizada como fonte.

Outro exemplo:

```text
Quais medicamentos das bulas disponíveis podem causar sonolência?
```

Esse exemplo testa uma consulta envolvendo múltiplas bulas.

---

## Consulta de filiais — Tool Calling

Experimente:

```text
Quais filiais de Londrina possuem estacionamento e Panvel Clinic?
```

Nesse caso, o sistema utiliza a tool `buscar_filiais` para consultar diretamente os dados estruturados de `filiais.parquet`.

---

## Contexto multi-turn

Primeiro envie:

```text
Quais filiais de Londrina possuem estacionamento e Panvel Clinic?
```

Depois:

```text
Dessas, quais possuem atendimento 24 horas?
```

A segunda mensagem deve preservar o contexto da primeira consulta.

---

## Consulta de filial específica

Experimente:

```text
Me fale sobre a filial 1740.
```

O sistema pode utilizar a tool `obter_filial` para consultar uma filial pelo código.

---

## Guardrail farmacológico

Experimente um medicamento que não pertence ao corpus:

```text
Quais são os efeitos adversos da amoxicilina?
```

O assistente deve informar que o medicamento não foi encontrado nas bulas disponíveis, em vez de gerar uma resposta farmacológica sem suporte no corpus.

Também é possível testar uma solicitação de orientação individual:

```text
Qual medicamento devo tomar para uma dor forte no peito?
```

O sistema não deve indicar medicamento, dose ou tratamento individualizado.

---

# Observabilidade

A interface permite visualizar detalhes da execução de cada resposta.

Entre as informações disponíveis estão:

- rota utilizada;
- query utilizada;
- tools chamadas;
- argumentos das tools;
- chunks recuperados;
- uso de tokens;
- latência;
- Trace ID.

Isso permite acompanhar como cada resposta foi produzida.

---

# Testes automatizados

O backend possui testes automatizados com Pytest.

Os testes utilizam mocks para integrações com LLM quando necessário, evitando consumo de tokens durante a suíte.

Para executar localmente, primeiro crie e ative um ambiente virtual:

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Depois:

```bash
pytest -v
```

Atualmente a suíte possui **31 testes automatizados** cobrindo funcionalidades como:

- health check;
- contrato OpenAPI;
- tools de filiais;
- validação dos argumentos das tools;
- identificação de medicamentos;
- chunking;
- roteamento;
- validações do assistente;
- guardrails farmacológicos.

---

# Estrutura do projeto

```text
Case_IA_Generativa/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── llm/
│   │   ├── models/
│   │   ├── observability/
│   │   ├── rag/
│   │   ├── services/
│   │   └── tools/
│   ├── scripts/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
│
├── data/
│   ├── corpus_bulas/
│   ├── filiais.parquet
│   └── dicionario_dados.xlsx
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

# Arquitetura resumida

```text
                    ┌─────────────────┐
                    │     Frontend    │
                    │ React + TS      │
                    └────────┬────────┘
                             │
                            SSE
                             │
                    ┌────────▼────────┐
                    │     FastAPI     │
                    └────────┬────────┘
                             │
                         Router
                    ┌────────┴────────┐
                    │                 │
                 FILIAIS            BULAS
                    │                 │
              Tool Calling        Guardrails
                    │                 │
             filiais.parquet         │
                                      ▼
                                  Retrieval
                                      │
                                   Qdrant
                                      │
                                      ▼
                                     LLM
```

Dados estruturados de filiais são consultados através de **tools**, enquanto documentos não estruturados, como as bulas, são consultados através de **RAG**.

---

# Encerrando a aplicação

Para parar os containers:

```bash
docker compose down
```

Para também apagar o volume persistido do Qdrant:

```bash
docker compose down -v
```

Na próxima inicialização após remover o volume, os embeddings serão gerados novamente.

---

# Documentação complementar

Para informações detalhadas sobre a arquitetura, decisões técnicas,
trade-offs e limitações, consulte:

- [Arquitetura Técnica](docs/ARCHITECTURE.md)
- [Recomendações Estratégicas](docs/STRATEGIC_RECOMMENDATIONS.md)