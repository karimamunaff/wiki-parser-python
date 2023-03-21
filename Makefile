CURRENT_PROJECT_VERSION = 0.1.0
DOCKER_CONTAINER_NAME = karimamunaff/wiki-parser-python-v$(CURRENT_PROJECT_VERSION)
LOCAL_DATA_DIRECTORY ?= data/
DOCKER_WORKING_DIRECTORY ?= /wiki-parser-python
DOCKER_DATA_DIRECTORY = $(DOCKER_WORKING_DIRECTORY)/data

.PHONY: build-image
build-image:
	docker build --build-arg WORKING_DIRECTORY=$(DOCKER_WORKING_DIRECTORY) --no-cache -t $(DOCKER_CONTAINER_NAME) .

.PHONY: setup_project
setup_project: build_image
	mkdir -p $(DATA_DIRECTORY)

.PHONY: enter-image
enter-image:
	docker run --rm -it --name wiki-parser-shell --mount source=$(LOCAL_DATA_DIRECTORY),target=$(DOCKER_DATA_DIRECTORY),type=bind $(DOCKER_CONTAINER_NAME)