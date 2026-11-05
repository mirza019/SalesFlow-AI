.PHONY: dev test

dev:
	docker compose up --build

test:
	pytest backend/tests
	cd frontend && npm test -- --run

