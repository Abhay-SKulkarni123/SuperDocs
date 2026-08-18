# SuperDocs

Document intelligence platform built for the SuperDocs engineering assessment.

## Tech Stack

- Python 3.10
- FastAPI
- React
- Vite
- PostgreSQL 16
- Docker Compose
- pytest
- ESLint

## Project Structure

```text
SuperDocs/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js
- npm
- Docker Desktop
- Git

### Install Dependencies

Create and activate the Python virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

### Environment

Create the local environment file:

```bash
cp .env.example .env
```

The local database connection is configured through `DATABASE_URL`.

### Database

Start PostgreSQL:

```bash
docker compose up -d
```

Check the database container:

```bash
docker compose ps
```

Verify PostgreSQL is accepting connections:

```bash
docker exec superdocs-postgres pg_isready -U superdocs -d superdocs
```

PostgreSQL runs on port `5432` inside the container and is exposed on port `5433` on the host.

### Run the Backend

Start the FastAPI development server:

```bash
uvicorn backend.app.main:app --reload
```

API:

`http://127.0.0.1:8000`

Swagger documentation:

`http://127.0.0.1:8000/docs`

OpenAPI specification:

`http://127.0.0.1:8000/openapi.json`

Health check:

`http://127.0.0.1:8000/health`

### Run the Frontend

From the project root:

```bash
cd frontend
npm run dev
```

Frontend:

`http://localhost:5173`

## Testing

Run the backend test suite from the project root:

```bash
pytest
```

The current test suite covers the application health endpoint and PostgreSQL connectivity.

## Frontend Build

Create a production build:

```bash
cd frontend
npm run build
```

## Environment Variables

The `.env` file is used for local configuration.

Example:

```env
APP_ENV=development
DATABASE_URL=postgresql://superdocs:superdocs_dev@localhost:5433/superdocs
OPENAI_API_KEY=
SUPERVISOR_API_KEY=
```

`.env` is ignored by Git and should never be committed.

## Development

The project is being developed incrementally across multiple phases. Each phase is completed and verified before moving to the next one.

The initial foundation includes:

- FastAPI backend
- React frontend
- PostgreSQL database
- Docker Compose configuration
- Database connectivity
- Health endpoint
- Backend tests
- Frontend health integration
- Frontend production build
- Development tooling and configuration

Further application functionality will be added in the subsequent assessment phases.