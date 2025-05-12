SHELL := /bin/bash

.PHONY: dev test lint build

dev:
	docker compose up --build -d

test:
	cd backend && pytest
	cd frontend && npm test

lint:
	cd backend && flake8 . && black --check . && isort --check-only .
	cd frontend && npm run lint

build:
	cd frontend && npm run build
