FROM python:2-slim
MAINTAINER Jannis Leidel <jezdez@mozilla.com>

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app/

EXPOSE 8000

# add a non-privileged user for installing and running the application
# don't use --create-home option to prevent populating with skeleton files
RUN mkdir /app && \
    chown 10001:10001 /app && \
    groupadd --gid 10001 app && \
    useradd --no-create-home --uid 10001 --gid 10001 --home-dir /app app

# install a few essentials and clean apt caches afterwards
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
RUN mkdir -p /opt/npm /opt/static && \
    chown -R 10001:10001 /opt

# Install Python dependencies
COPY requirements.txt /tmp/
# Switch to /tmp to install dependencies outside home dir
WORKDIR /tmp
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Install frontend dependencies using NPM
COPY package.json /opt/npm/

# Switch to /opt/npm to install dependencies outside home dir
WORKDIR /opt/npm
RUN npm install && \
    chown -R 10001:10001 /opt/npm && \
    npm cache clean

# Switch back to home directory
WORKDIR /app

COPY . /app

RUN chown -R 10001:10001 /app

USER 10001
