.PHONY: dev dev-backend dev-frontend test test-backend test-frontend build docker-up docker-down clean

# Development
dev: dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && pytest -v

test-frontend:
	cd frontend && npm test

# Build
build:
	cd frontend && npm run build

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Clean
clean:
	rm -rf frontend/node_modules frontend/.next backend/__pycache__ backend/app/__pycache__ backend/app/api/__pycache__ backend/app/core/__pycache__ backend/tests/__pycache__
