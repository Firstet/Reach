.PHONY: up down dev logs backend-shell db-shell migrate ingest test prod-up prod-down check-deploy generate-keys

## Start full stack (detached)
up:
	docker-compose up -d

## Stop all services
down:
	docker-compose down

## Build and restart all services
rebuild:
	docker-compose up -d --build

## Start full production stack
prod-up:
	docker-compose -f docker-compose.prod.yml up -d --build

## Stop full production stack
prod-down:
	docker-compose -f docker-compose.prod.yml down

## Show streaming logs
logs:
	docker-compose logs -f backend worker

## Open a backend Python shell
backend-shell:
	docker-compose exec backend python

## Open a database psql shell
db-shell:
	docker-compose exec postgres psql -U reach -d reach

## Run Alembic migrations
migrate:
	docker-compose exec backend alembic upgrade head

## Ingest the RayvenSC knowledge base (requires a running backend)
ingest:
	@TOKEN=$$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
		-H 'Content-Type: application/json' \
		-d '{"email":"admin@rayvensc.com","password":"$(ADMIN_PASSWORD)"}' \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	curl -s -X POST http://localhost:8000/api/v1/knowledge/ingest \
		-H "Authorization: Bearer $$TOKEN" | python3 -m json.tool

## Run backend unit tests
test:
	cd backend && python -m pytest tests/unit/ -v

## Run deployment readiness check
check-deploy:
	PYTHONPATH=backend backend/.venv/bin/python scripts/check_deployment.py

## Generate secure secrets for .env
generate-keys:
	@backend/.venv/bin/python -c "import secrets; from cryptography.fernet import Fernet; print('APP_SECRET_KEY=' + secrets.token_hex(32)); print('JWT_SECRET_KEY=' + secrets.token_hex(32)); print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

## Start the frontend dev server only
frontend-dev:
	cd frontend && npm run dev

## Check provider health
health:
	@TOKEN=$$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
		-H 'Content-Type: application/json' \
		-d '{"email":"admin@rayvensc.com","password":"$(ADMIN_PASSWORD)"}' \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	curl -s http://localhost:8000/api/v1/config/health \
		-H "Authorization: Bearer $$TOKEN" | python3 -m json.tool

## View the API docs (development only)
docs:
	open http://localhost:8000/api/docs

