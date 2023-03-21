CURRENT_PROJECT_VERSION = 0.1.0
USE_DOCKER ?= 1 # Set this to 1 if you want to use Docker
DOCKER_IMAGE_NAME = karimamunaff/wiki-parser-python-v$(CURRENT_PROJECT_VERSION)
LOCAL_DATA_DIRECTORY ?= $(CURDIR)/data/
DOCKER_WORKING_DIRECTORY ?= /wiki-parser-python
DOCKER_DATA_DIRECTORY = $(DOCKER_WORKING_DIRECTORY)/data
DOCKER_CONTAINER_NAME ?= wiki-parser-shell

.make/build-image:
	docker build --build-arg WORKING_DIRECTORY=$(DOCKER_WORKING_DIRECTORY) --no-cache -t $(DOCKER_IMAGE_NAME) .
	touch $@

.PHONY: setup_project
setup_project:
	mkdir -p $(LOCAL_DATA_DIRECTORY)
	mkdir -p .make
	if [[ $(USE_DOCKER) == 1 ]]; then \
		$(MAKE) build-image ;\
	else \
		poetry update ;\
	fi

define run_command
	## ----------------------------------------------------------------------
	## This function runs bash commands with or without docker
	## set USE_DOCKER=1 while calling targets to run commands using docker
	## Running commands in docker follows three steps
	## 1. Start and Run Docker Container, 
	## 2. Run Commands in Container
	## 3. Remove Container
	## ----------------------------------------------------------------------
	if [[ $(USE_DOCKER) == 1 ]]; then \
		docker run -dit --name $(DOCKER_CONTAINER_NAME) --mount source=$(LOCAL_DATA_DIRECTORY),target=$(DOCKER_DATA_DIRECTORY),type=bind $(DOCKER_IMAGE_NAME);\
		docker exec $(DOCKER_CONTAINER_NAME) ${1} ;\
		docker rm -f $(DOCKER_CONTAINER_NAME) ;\
	else \
		eval ${1} ;\
	fi
endef

.PHONY: enter-image
enter-image: .make/build-image
	docker run --rm -it --name $(DOCKER_CONTAINER_NAME) --mount source=$(LOCAL_DATA_DIRECTORY),target=$(DOCKER_DATA_DIRECTORY),type=bind $(DOCKER_IMAGE_NAME);

.PHONY: test
test:
	@$(call run_command, which python)