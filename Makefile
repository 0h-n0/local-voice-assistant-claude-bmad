.PHONY: dev dev-frontend dev-backend lint test clean setup

# Development - run frontend and backend in parallel
dev:
	@echo "Starting development servers..."
	make -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uv run uvicorn voice_assistant.main:app --reload --host 0.0.0.0 --port 8000

# Linting
lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

lint-fix:
	cd backend && uv run ruff check . --fix
	cd frontend && npm run lint -- --fix

# Testing
test:
	cd backend && uv run pytest
	cd frontend && npm test

test-backend:
	cd backend && uv run pytest -v

test-frontend:
	cd frontend && npm test

# Setup
setup:
	./scripts/setup.sh

# Cleanup
clean:
	rm -rf frontend/.next frontend/node_modules
	rm -rf backend/.venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
