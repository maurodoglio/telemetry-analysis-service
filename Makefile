.PHONY: build clean creds migrate redis-cli revision shell stop test up

help:
	@echo "Welcome to the Telemetry Analysis Service\n"
	@echo "The list of commands for local development:\n"
	@echo "  build      Builds the docker images for the docker-compose setup"
	@echo "  ci         Run the test with the CI specific Docker setup"
	@echo "  clean      Stops and removes all docker containers"
	@echo "  creds CLIENT_ID=<CLIENT_ID> CLIENT_SECRET=<CLIENT_SECRET>"
	@echo "             Sets the Google Credentials required for authentication"
	@echo "  migrate    Runs the Django database migrations"
	@echo "  redis-cli  Opens a Redis CLI"
	@echo "  shell      Opens a Bash shell"
	@echo "  test       Runs the Python test suite"
	@echo "  up         Runs the whole stack, served under http://localhost:8000/\n"
	@echo "  stop       Stops the docker containers"

build:
	docker-compose build

ci:
	docker-compose -f docker-compose.yml run web bin/run tests

clean: stop
	docker-compose rm -f

creds:
	@docker-compose run web ./manage.py add_google_credentials \
	--client-id="$(CLIENT_ID)" --client-secret="$(CLIENT_SECRET)"

migrate:
	docker-compose run web python manage.py migrate --run-syncdb

shell:
	docker-compose run web bash

redis-cli:
	docker-compose run redis redis-cli -h redis

stop:
	docker-compose stop

test:
	docker-compose run web bin/run tests

up:
	docker-compose up
