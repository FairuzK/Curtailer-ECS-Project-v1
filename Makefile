.PHONY: venv run test docker-build docker-run

venv:
	python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

run:
	cd src && DB_PATH=../data/urls.db ../.venv/bin/python -m flask --app shortener:create_app run --port 8000 --debug

test:
	.venv/bin/pytest -q

# --platform linux/amd64 matters on Apple Silicon: the Fargate task is X86_64
docker-build:
	docker build --platform linux/amd64 --build-arg APP_VERSION=local -t url-shortener:local .

docker-run:
	docker run --rm -p 8000:8000 url-shortener:local
