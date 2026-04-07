# Case-Study-2


## Docker VM setup:
To run docker containers from VM

```bash
./backend_docker_deploy.sh # Backend setup 
./frontend_docker_deploy.sh # Frontend setup
```

Then once containers are running:

Frontend (app): http://paffenroth-23.dyn.wpi.edu:22091

Backend (FastAPI Docs/API): http://paffenroth-23.dyn.wpi.edu:22092/docs 

Prometheus (Monitoring): http://paffenroth-23.dyn.wpi.edu:22094


## Local Setup
In frontend docker file 
```bash
# Update this line:
ENV NEXT_PUBLIC_BACKEND_URL=http://localhost:22092
```

In prometheus.yml make the following updates
```bash 
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cs3-backend'
    scrape_interval: 5s
    static_configs:
      - targets: ['host.docker.internal:22092']
```

Run
```bash
# Build the backend image
docker build -t cs3-backend -f backend/Dockerfile .

docker run -d --name cs3-backend -p 22092:22092 -e HF_TOKEN="your_actual_token_here" -v cs3-backend-uploads:/opt/app/uploads -v cs3-backend-db:/opt/app/db cs3-backend

# Build the frontend image
docker build -t cs3-frontend -f shrug-intelligence/Dockerfile shrug-intelligence/

# Run frontend container 
docker run -d --name cs3-frontend -p 22091:22091 cs3-frontend

# Run prometheus container
docker run -d --name prometheus -p 22094:9090 -v "path/to/prometheus.yml:/etc/prometheus/prometheus.yml:ro" prom/prometheus
```
App: http://localhost:22091

Backend API Docs: http://localhost:22092/docs

Prometheus: http://localhost:22094


## Local Development
`backend`
- `uv run pytest tests`: test cases
- `uv run db.database`: populates database (WIP)
- `uv run fastapi dev routes`: runs localhost routes

`Windows Local Backend` 
- python -m backend.db.database
- python -m uvicorn backend.routes:app --reload --port 8000


`shrug-intelligence`
- `bun run dev`
- `bun run start`
