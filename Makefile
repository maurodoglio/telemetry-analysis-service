.PHONY: build clean migrate shell static test up

build:
	docker-compose build

clean:
	docker-compose rm -f
	rm -rf static/

migrate:
	docker-compose run web ./manage.py migrate --run-syncdb

shell:
	docker-compose run web bash

static:
	# this is only necessary after adding/removing/editing static files
	docker-compose run web ./manage.py collectstatic --noinput

test: static
	docker-compose run web ./manage.py test

up:
	docker-compose up
