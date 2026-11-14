# AI Customer Support System

An AI-powered customer support application combining **machine learning intent classification, Retrieval-Augmented Generation (RAG), Large Language Model (LLM) response generation, and human-in-the-loop review**.

The system processes customer support messages, predicts their intent, retrieves relevant support policies, and generates policy-grounded response suggestions. Support staff can review, approve, edit, or reject AI-generated responses through a Streamlit dashboard.

The project demonstrates an end-to-end AI customer support workflow, from ticket classification and knowledge retrieval to response generation and human approval.

## Key Features

- **ML-based intent classification:** Classifies customer messages into shipping, refund, and payment categories using TF-IDF and Logistic Regression.
- **Confidence-based review:** Uses prediction confidence and the margin between the two highest class scores to identify uncertain predictions.
- **Retrieval-Augmented Generation:** Retrieves relevant support policies using Sentence Transformers and PostgreSQL with pgvector.
- **LLM response generation:** Uses Qwen 2.5 3B through Ollama to generate responses grounded in retrieved knowledge.
- **AI agent orchestration:** Coordinates classification, retrieval, answer generation, and review decisions in a unified support workflow.
- **Human-in-the-loop review:** Allows support agents to approve, edit and approve, or reject generated answers.
- **REST API:** FastAPI exposes endpoints for ticket management, classification, knowledge retrieval, and support processing.
- **Staff dashboard:** Streamlit provides an interface for interacting with tickets and reviewing AI suggestions.
- **Authentication:** JWT-based authentication protects staff operations.
- **Evaluation and testing:** Includes classifier tests, support workflow tests, and RAG evaluation scripts.

## Architecture

```text
                 Customer Support Ticket
                           |
                           v
                    FastAPI Backend
                           |
                           v
                Support Agent Orchestrator
                           |
              +------------+------------+
              |                         |
              v                         v
       Intent Classifier           RAG Retrieval
       TF-IDF + Logistic           Sentence Transformers
       Regression                  + PostgreSQL/pgvector
              |                         |
              v                         v
       Intent Category             Relevant Policies
              |                         |
              +------------+------------+
                           |
                           v
                    LLM Generation
                    Qwen 2.5 3B
                    via Ollama
                           |
                           v
                 Generated Answer
                           |
                           v
                    Human Review
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Approve         Edit         Reject
             |             |             |
             +-------------+-------------+
                           |
                           v
                    PostgreSQL
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend API | FastAPI |
| ML classification | Scikit-learn |
| Text features | Word and character TF-IDF |
| Classification algorithm | Logistic Regression |
| Embeddings | Sentence Transformers |
| Vector database | PostgreSQL + pgvector |
| Local LLM | Qwen 2.5 3B |
| LLM runtime | Ollama |
| Dashboard | Streamlit |
| Database access | Psycopg |
| Authentication | JWT |
| Testing | Pytest |
| Version control | Git and GitHub |

## Project Structure

```text
ai-support-engineer/
│
├── app/
│   ├── agents/
│   │   └── support_agent.py
│   │
│   ├── auth/
│   │   ├── dependencies.py
│   │   ├── routes.py
│   │   └── security.py
│   │
│   ├── evaluation/
│   │   └── evaluate.py
│   │
│   ├── models/
│   │   ├── predict.py
│   │   └── train.py
│   │
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   └── search.py
│   │
│   ├── config.py
│   ├── db.py
│   ├── generator.py
│   ├── main.py
│   ├── predictor.py
│   ├── predictor_v2.py
│   └── retriever.py
│
├── artifacts/
│   ├── intent_classifier.joblib
│   └── intent_classifier_v2.joblib
│
├── data/
│   ├── raw/
│   │   └── knowledge_base.csv
│   │
│   └── processed/
│       ├── support_training_v2.csv
│       ├── rag_evaluation.csv
│       ├── rag_retrieval_results.csv
│       └── rag_answer_results_v2.csv
│
├── db/
│   ├── schema.sql
│   └── seed.sql
│
├── scripts/
│   ├── ingest_knowledge.py
│   ├── train_classifier_v2.py
│   ├── evaluate_rag_retrieval.py
│   └── evaluate_rag_answers_v2.py
│
├── tests/
│   ├── test_predict_v2.py
│   └── test_support_process.py
│
├── dashboard.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```

## How It Works

### 1. Intent Classification

The system classifies customer support messages into three categories:

- `shipping`
- `refund`
- `payment`

The V2 classifier uses a combined word-level and character-level TF-IDF feature representation with Logistic Regression.

In addition to predicting an intent, the classifier evaluates the model's confidence and the margin between the two highest class scores.

These signals help identify uncertain predictions that may require additional review.

Two trained model artifacts are included:

- `intent_classifier.joblib`
- `intent_classifier_v2.joblib`

### 2. Knowledge Retrieval

The retrieval component uses Sentence Transformers to convert support policies and customer queries into vector embeddings.

These embeddings are stored in PostgreSQL with the pgvector extension.

When a customer submits a message, the system searches the knowledge base for semantically relevant policies using vector similarity.

The retrieved documents provide supporting context for answer generation.

### 3. LLM Answer Generation

The generation component uses Qwen 2.5 3B through Ollama.

The LLM receives the customer message and relevant retrieved policy content to generate a suggested support response.

The purpose of retrieval is to ground the generated answer in the available support knowledge rather than relying only on the model's general knowledge.

### 4. AI Agent Orchestration

The support agent coordinates the complete workflow:

1. Receives the customer message.
2. Predicts the support intent.
3. Retrieves relevant knowledge-base documents.
4. Generates a suggested response.
5. Determines whether the result should proceed to human review.
6. Returns the result for staff review.

The orchestration logic is implemented in:

`app/agents/support_agent.py`

### 5. Human-in-the-Loop Review

AI-generated responses are suggestions, not automatically approved customer communications.

Support staff can:

- **Approve:** Accept the suggested response.
- **Edit and approve:** Modify the response before accepting it.
- **Reject:** Reject the generated response.

Review decisions are handled through the backend and persisted in the database.

This design keeps human oversight within the support workflow.

## Installation and Setup

### Prerequisites

Install the following software before running the application:

- Python 3.10 or later
- PostgreSQL with the pgvector extension
- Ollama
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/shreyasgudigar/ai-support-engineer.git
cd ai-support-engineer
```

### 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local `.env` file using the environment-variable names expected by `app/config.py` and the database configuration.

Configure the following settings as applicable:

- PostgreSQL connection details
- JWT secret key
- Authentication settings
- Ollama service URL
- LLM model name

Do not commit `.env` or expose database passwords and JWT secrets in the repository.

### 5. Configure PostgreSQL

Create a PostgreSQL database and ensure the pgvector extension is installed.

The database initialization files are located in:

```text
db/schema.sql
db/seed.sql
```

Apply the schema and seed data to initialize the database before running database-dependent application features.

### 6. Configure Ollama

Install Ollama and download the model:

```bash
ollama pull qwen2.5:3b
```

Start the Ollama service and ensure the application can reach its configured Ollama endpoint.

The LLM generation component depends on this service when using the local model.

### 7. Start the FastAPI Backend

From the project root:

```bash
uvicorn app.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 8. Start the Streamlit Dashboard

Open another terminal, activate the virtual environment, and run:

```bash
streamlit run dashboard.py
```

The dashboard is normally available at:

```text
http://localhost:8501
```

The dashboard communicates with the FastAPI backend using its configured API URL.

## API Endpoints

The FastAPI backend exposes the following main routes:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API root |
| GET | `/tickets` | Retrieve support tickets |
| POST | `/predict` | Run intent classification |
| POST | `/predict/v2` | Run V2 intent classification |
| GET | `/knowledge/search` | Search support knowledge |
| POST | `/support/process` | Run the AI support workflow |
| POST | `/.../approve` | Approve a generated answer |
| POST | `/.../edit-approve` | Edit and approve an answer |
| POST | `/.../reject` | Reject a generated answer |

The approval routes are grouped under the ticket workflow in the application. Refer to the interactive API documentation at `/docs` for their exact paths, request schemas, and authentication requirements.

## Training and Knowledge Ingestion

The repository includes scripts for maintaining the classifier and knowledge base.

### Train the V2 Classifier

```bash
python scripts/train_classifier_v2.py
```

The training workflow uses the processed V2 training dataset and produces the V2 classifier artifact.

### Ingest Knowledge-Base Documents

```bash
python scripts/ingest_knowledge.py
```

This script loads knowledge-base content into the configured retrieval database.

Run database initialization before ingestion.

## Evaluation

The project includes evaluation workflows for both classification and retrieval-augmented generation.

### RAG Retrieval Evaluation

```bash
python scripts/evaluate_rag_retrieval.py
```

Evaluates whether relevant support documents are retrieved for a set of test queries.

### RAG Answer Evaluation

```bash
python scripts/evaluate_rag_answers_v2.py
```

Evaluates generated answers against a curated set of support questions and expected knowledge.

### Automated Tests

Run the test suite using:

```bash
pytest -v
```

The tests cover intent prediction and the support-processing workflow.

## Evaluation Results

The project includes saved evaluation outputs under `data/processed/`, including:

- `rag_evaluation.csv`
- `rag_retrieval_results.csv`
- `rag_answer_results_v2.csv`

The retrieval evaluation includes a curated set of 30 questions. In that evaluation, the expected documents were retrieved within the top five results for all 27 queries with an expected document.

These results demonstrate performance on the evaluated dataset. They should not be interpreted as a guarantee of retrieval quality across all real-world customer support queries.

## Design Considerations

### Human Oversight

The system treats generated answers as suggestions that require staff review rather than automatically sending every AI response to customers.

### Policy-Grounded Generation

Relevant knowledge-base content is retrieved before answer generation to provide policy context.

### Confidence-Based Review

The classifier uses confidence and prediction-margin signals to identify uncertain predictions.

### Modular Architecture

Classification, retrieval, generation, authentication, API routing, and dashboard functionality are separated into application modules.

This makes individual components easier to maintain, test, and improve.

## Current Limitations

- The classifier currently supports three intent categories: shipping, refund, and payment.
- Classification confidence scores are model outputs and are not necessarily calibrated probabilities.
- The retrieval evaluation uses a limited curated dataset and does not establish performance on every possible customer query.
- Generated answers depend on the quality and coverage of the knowledge base.
- The local Qwen model requires Ollama to be running and accessible.
- The local LLM configuration is not automatically available in a cloud deployment. A cloud deployment requires an accessible hosted inference service or a separately configured generation strategy.
- PostgreSQL with pgvector must be configured before database-backed retrieval and ticket operations can work.

## Future Improvements

- Expand intent classification to additional support categories.
- Improve classifier calibration and out-of-distribution detection.
- Expand retrieval and answer evaluation datasets.
- Add monitoring for retrieval quality and generated-answer quality.
- Integrate a hosted LLM provider for cloud deployment.
- Add more comprehensive authentication, authorization, and audit logging.
- Improve deployment automation and production observability.

## Project Goals

This project demonstrates practical implementation of:

- Machine learning for text classification.
- Semantic search and vector databases.
- Retrieval-Augmented Generation.
- Local LLM integration.
- AI agent orchestration.
- Human-in-the-loop AI workflows.
- REST API development.
- Database-backed applications.
- Testing and evaluation of AI components.

## Author

**Shreyas Gudigar**

GitHub: [https://github.com/shreyasgudigar](https://github.com/shreyasgudigar)

Project Repository: [https://github.com/shreyasgudigar/ai-support-engineer](https://github.com/shreyasgudigar/ai-support-engineer)