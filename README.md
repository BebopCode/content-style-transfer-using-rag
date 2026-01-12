Readme · MD
Copy

# Content Style Transfer Using RAG

## Prerequisites

- Docker and Docker Compose installed on your system
- Git
- Gemini API key

## Installation

### 1. Clone the Repository

```bash
git clone 
cd content-style-transfer-using-rag
```

### 2. Environment Configuration

#### Backend Environment Variables

Create a `.env` file in the `web-app/` directory:

```
GEMINI_API_KEY=your_gemini_api_key_here
PASSWORD=sample_password
```

#### Frontend Environment Variables

Create a `.env.local` file in the `web-app/frontend/` directory:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Add Email Data

Place your email files in `.eml` format into the following directory:

```
web-app/backend/app/data_emails/
```

The application will process these emails during startup.

## Running the Application

### Build and Start Containers

From the root directory, run:

```bash
docker compose up --build
```

This command will build the Docker images and start all containers.

### Monitoring Database Generation

To view the logs of the database generation process, use:

```bash
docker logs 
```

## Accessing the Application

Once the containers are running, access the application at:

- **Frontend:** http://localhost:3000 (default Next.js port)

## Project Structure

```
.
├── experiments/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── enron.py
│   ├── pipeline.py
│   └── evaluator.py
└── web-app/
    ├── .env
    ├── docker-compose.yml
    ├── backend/
    │   └── app/
    │       └── data_emails/
    └── frontend/
        └── .env.local
```

---

## Running Experiments

The `experiments/` folder contains scripts for running experiments with the style transfer pipeline.

### Prerequisites for Experiments

- An Ollama endpoint running and accessible
- Docker installed

### Configuration

The experiments use build arguments to configure the pipeline. You can customize these when building the Docker image:

| Argument | Default | Description |
|----------|---------|-------------|
| `NUMBER_OF_SAMPLE_EMAILS` | 2 | Number of sample emails to process |
| `GENERATOR_MODEL_NAME` | ministral | Model name for generation |
| `RETRIEVED_EMAILS` | 5 | Number of emails to retrieve |
| `EVALUATOR_MODEL_NAME` | ministral-3:8b | Model name for evaluation |
| `BASE_URL` | http://localhost:11434 | Base URL for the Ollama API |

### Building and Running Experiments

```bash
cd experiments
docker build -t experiments .
docker run --rm experiments
```
