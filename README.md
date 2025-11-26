Prerequisites

- Docker and Docker Compose installed on your system
- Git
- Gemini API key

## Installation

### 1. Clone the Repository
```bash
git clone 
cd 
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
PASSWORD=password!123
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
docker-compose up --build
```

This command will build the Docker images and start all containers.

### Monitoring Database Generation

To view the logs of the database generation process, use:
```bash
docker logs <container-id>
```

## Accessing the Application

Once the containers are running, access the application at:

- Frontend: `http://localhost:3000` (default Next.js port)



## Project Structure
```
.
└── web-app/
    ├── .env
    ├── docker-compose.yml
    ├── backend/
    │   └── app/
    │       └── data_emails/
    └── frontend/
        └── .env.local