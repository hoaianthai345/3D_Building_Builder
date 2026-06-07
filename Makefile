.PHONY: backend frontend test frontend-build docker

backend:
	. .venv/bin/activate && uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

test:
	. .venv/bin/activate && pytest
	cd frontend && npx tsc --noEmit

frontend-build:
	cd frontend && npm run build

docker:
	docker compose up --build
