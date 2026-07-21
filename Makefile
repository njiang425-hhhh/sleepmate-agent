.PHONY: dev dev-backend dev-frontend test test-backend test-frontend test-e2e check build docker-up docker-down docker-up-prod docker-smoke clean

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

test-e2e:
	cd frontend && npx playwright test

# Lint & format
check: test-backend test-frontend test-e2e

# Build
build:
	cd frontend && npm run build

# Docker (development)
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Docker (production)
docker-up-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Docker smoke test
docker-smoke:
	@echo "=== Docker Smoke Test ==="
	@echo "1. Checking backend health..."
	@curl -sf http://localhost:8000/api/v1/health || (echo "FAIL: backend health" && exit 1)
	@echo " OK"
	@echo "2. Checking frontend..."
	@curl -sf http://localhost:3000 > /dev/null || (echo "FAIL: frontend" && exit 1)
	@echo " OK"
	@echo "3. Checking TTS endpoint..."
	@curl -sf -X POST http://localhost:8000/api/v1/audio/tts -H "Content-Type: application/json" -d '{"script_text":"test"}' > /dev/null || (echo "FAIL: TTS" && exit 1)
	@echo " OK"
	@echo "=== All smoke tests passed ==="

# Clean
clean:
	rm -rf frontend/node_modules frontend/.next backend/__pycache__ backend/app/__pycache__ backend/app/api/__pycache__ backend/app/core/__pycache__ backend/tests/__pycache__
