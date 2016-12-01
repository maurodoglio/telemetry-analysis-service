FROM python:2-slim
MAINTAINER Mozilla Telemetry <telemetry-analysis-service@mozilla.org>

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app/

EXPOSE 8000

# add a non-privileged user for installing and running the application
RUN mkdir /app && \
    chown 10001:0 /app && \
    chmod g+w /app && \
    groupadd --gid 10001 app && \
    useradd --uid 10001 --gid 0 --home /app app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-transport-https build-essential curl git libpq-dev \
        postgresql-client gettext sqlite3 libffi-dev  && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install node from NodeSource
RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
    echo 'deb https://deb.nodesource.com/node_4.x jessie main' > /etc/apt/sources.list.d/nodesource.list && \
    echo 'deb-src https://deb.nodesource.com/node_4.x jessie main' >> /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && apt-get install -y nodejs

# Create static and npm roots
RUN mkdir -p /opt/coverage /opt/npm /opt/static && \
    chown -R 10001:0 /opt && \
    chmod -R g+w /opt

# Switch to /tmp to install dependencies outside home dir
WORKDIR /tmp

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Switch to /opt/npm to install dependencies outside home dir
WORKDIR /opt/npm

# Install frontend dependencies using NPM
COPY package.json /opt/npm/
RUN npm install && \
    chown -R 10001:0 /opt/npm && \
    chmod -R g+w /opt/npm

# Switch back to home directory
WORKDIR /app

COPY . /app

RUN chown -R 10001:0 /app && \
    chmod -R g+w /app

USER 10001
