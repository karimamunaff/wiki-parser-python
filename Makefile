CURRENT_VERSION = 0.1.0
DOCKER_CONTAINER_NAME = karimamunaff/wiki-parser-python-v$(CURRENT_VERSION)
LOCAL_DATA_DIRECTORY ?= data/
DOCKER_WORKING_DIRECTORY ?= /wiki-parser-python

.PHONY: build-image
build-image:
	docker build --build-arg WORKING_DIRECTORY=$(DOCKER_WORKING_DIRECTORY) --no-cache -t $(DOCKER_CONTAINER_NAME) .

.PHONY: enter-image
enter-image:
	docker run --rm -it --name wiki-parser-shell $(DOCKER_CONTAINER_NAME) --mount type=bind,source=$(LOCAL_DATA_DIRECTORY),target=$(DOCKER_WORKING_DIRECTORY)/data/
