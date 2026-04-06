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
