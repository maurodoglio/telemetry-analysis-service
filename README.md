analysis_service
==========

[![Build Status](https://travis-ci.org/maurodoglio/telemetry-analysis-service.svg?branch=master)](https://travis-ci.org/maurodoglio/telemetry-analysis-service)

[![Coverage status](https://img.shields.io/coveralls/maurodoglio/telemetry-analysis-service/master.svg)](https://coveralls.io/r/maurodoglio/telemetry-analysis-service)

Run the tests
-------------

There's a sample test in `analysis_service/base/tests.py` for your convenience, that you can run using the following command:

    docker-compose run web ./manage.py test

If you want to run the full suite, with flake8 and coverage, you may use
[tox](https://testrun.org/tox/latest/). This will run the tests the same way
they are run by [travis](https://travis-ci.org)):

    pip install tox
    tox

The `.travis.yml` file will also run [coveralls](https://coveralls.io) by
default.

If you want to benefit from Travis and Coveralls, you will need to activate
them both for your project.

Oh, and you might want to change the "Build Status" and "Coverage Status" links
at the top of this file to point to your own travis and coveralls accounts.

Development Setup
-----------------

This application is packaged with Docker, which manages and maintains a consistent application environment.

On a Debian-derived Linux distributions, run `./build.sh` in the project root directory to perform all the installation steps automatically. On other OSs, [install Docker](https://docs.docker.com/mac/) and [Docker Compose](https://docs.docker.com/compose/install/) manually.

To start the application, run `docker-compose up`.

Quick troubleshooting guide:

* Docker gives an error message similar to `ERROR: Couldn't connect to Docker daemon at http+docker://localunixsocket - is it running?`
    * Run the command as administrator/superuser (for testing purposes, that is).
    * Make sure the user is in the `docker` group (use the `sudo usermod -aG docker ${USER}` command to do this). This allows the user to use Docker without superuser privileges. Note that this does not take effect until the user logs out and logs in again.
* Docker gives an error message similar to `Err http://security.debian.org jessie/updates InRelease`
    * The installed Docker version is possibly too old. Make sure to use the latest available stable version.
    * Ensure that the DNS configuration is sane: `docker-compose run web ping security.debian.org`.

Production Setup
----------------

1. Add your project in [Docker Registry](https://registry.hub.docker.com/) as [Automated Build](http://docs.docker.com/docker-hub/builds/)
2. Prepare a 'env' file with all the variables needed by dev, stage or production.
3. Run the image:

    docker run --env-file env -p 80:8000 mozilla/analysis_service

Heroku Setup
------------
1. heroku create
2. heroku config:set DEBUG=False ALLOWED_HOSTS=<foobar>.herokuapp.com, SECRET_KEY=something_secret
   DATABASE_URL gets populated by heroku once you setup a database.
3. git push heroku master

NewRelic Monitoring
-------------------

A newrelic.ini file is already included. To enable NewRelic monitoring
add two enviroment variables:

 - NEW_RELIC_LICENSE_KEY
 - NEW_RELIC_APP_NAME

See the [full list of supported environment variables](https://docs.newrelic.com/docs/agents/python-agent/installation-configuration/python-agent-configuration#environment-variables).
