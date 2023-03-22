CURRENT_PROJECT_VERSION = '0.1.0'
DOCKER_IMAGE_NAME = 'karimamunaff/wiki-parser-python-v$(CURRENT_PROJECT_VERSION)'
DOCKER_CONTAINER_NAME ?= 'wiki-parser-shell'

LOCAL_DATA_DIRECTORY ?= '$(CURDIR)/data/'
DOCKER_WORKING_DIRECTORY ?= '/wiki-parser-python'
DOCKER_DATA_DIRECTORY = '$(DOCKER_WORKING_DIRECTORY)/data' # mount LOCAL_DATA_DIRECTORY to this in Docker

$(eval COMPLETED_DUMPDATE := $(shell export PYTHONPATH="${PYTHONPATH}:$$CURDIR../../" && poetry run python -c 'from src.get_latest_wikidate import get_date; print(get_date())'))
WIKI_DUMP_DATE ?= $(COMPLETED_DUMPDATE)
WIKIPEDIA_DOWNLOAD_URL = 'https://dumps.wikimedia.org/enwiki/$(WIKI_DUMP_DATE)/enwiki-$(WIKI_DUMP_DATE)-pages-articles-multistream.xml.bz2'
WIKIPEDIA_INDEX_DOWNLOAD_URL = 'https://dumps.wikimedia.org/enwiki/$(WIKI_DUMP_DATE)/enwiki-$(WIKI_DUMP_DATE)-pages-articles-multistream-index.txt.bz2'
WIKIPEDIA_DOWNLOAD_DIRECTORY = '$(LOCAL_DATA_DIRECTORY)/wikipedia/$(WIKI_DUMP_DATE)/'

.make/build-image:
	docker build --build-arg WORKING_DIRECTORY=$(DOCKER_WORKING_DIRECTORY) --no-cache -t $(DOCKER_IMAGE_NAME) .
	touch $@

.PHONY: setup_project
setup_project:
	mkdir -p $(WIKIPEDIA_DOWNLOAD_DIRECTORY)
	mkdir -p .make
	$(MAKE) .make/build-image

define run_command_in_docker
	## ----------------------------------------------------------------------
	## This function runs bash commands in docker
	## Running commands in docker follows three steps
	## 1. Start and Run Docker Container, 
	## 2. Run Commands in Container
	## 3. Remove Container
	## ----------------------------------------------------------------------
	docker rm -f $(DOCKER_CONTAINER_NAME)
	docker run -dit -it --name $(DOCKER_CONTAINER_NAME) --mount type=bind,source=$(LOCAL_DATA_DIRECTORY),target=$(DOCKER_DATA_DIRECTORY) $(DOCKER_IMAGE_NAME)
	docker exec $(DOCKER_CONTAINER_NAME) ${1}
	docker rm -f $(DOCKER_CONTAINER_NAME)
endef

.PHONY: enter-image
enter-image: .make/build-image
	docker run --rm -it --name $(DOCKER_CONTAINER_NAME) --mount type=bind,source=$(LOCAL_DATA_DIRECTORY),target=$(DOCKER_DATA_DIRECTORY) $(DOCKER_IMAGE_NAME)

.PHONY: download_wikipedia
download_wikipedia:
	wget --continue --directory-prefix=$(WIKIPEDIA_DOWNLOAD_DIRECTORY) $(WIKIPEDIA_DOWNLOAD_URL)
	wget --continue --directory-prefix=$(WIKIPEDIA_DOWNLOAD_DIRECTORY) $(WIKIPEDIA_INDEX_DOWNLOAD_URL)

.PHONY: format
format: 
	poetry run black .
	poetry run isort .