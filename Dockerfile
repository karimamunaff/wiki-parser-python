
# Build from Python Image
FROM python:3.10.10-slim-bullseye

ARG WORKING_DIRECTORY="/wiki-parser-python"

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1
# Poetry version
ENV POETRY_VERSION=1.4.0

# Copy project files to docker working directory
WORKDIR $WORKING_DIRECTORY
COPY . $WORKING_DIRECTORY

# # Install system essentials
RUN apt-get update 
RUN apt-get -y install build-essential
RUN apt-get -y install tmux
RUN pip install -U pip

# install poetry
RUN pip install -U "poetry==$POETRY_VERSION"

# install python packages
RUN poetry install --no-interaction --no-ansi

ENTRYPOINT bash
