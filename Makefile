CURRENT_PROJECT_VERSION = '0.1.0'
DOCKER_IMAGE_NAME = 'karimamunaff/wiki-parser-python-v$(CURRENT_PROJECT_VERSION)'
DOCKER_CONTAINER_NAME ?= 'wiki-parser-shell'

DATA_DIRECTORY ?= '$(CURDIR)/data/'
DOCKER_WORKING_DIRECTORY = '/wiki-parser-python'
TEST_COVERAGE_REPORT_DIRECTORY = 'documentation/docs/test_coverage_report'

$(eval COMPLETED_DUMPDATE := $(shell export PYTHONPATH="${PYTHONPATH}:$$CURDIR../../" && poetry run python -c 'from src.extract_dumpdate import get_recent_common; print(get_recent_common())'))
WIKI_DUMP_DATE ?= $(COMPLETED_DUMPDATE)
WIKIPEDIA_DOWNLOAD_URL = 'https://dumps.wikimedia.org/enwiki/$(WIKI_DUMP_DATE)/enwiki-$(WIKI_DUMP_DATE)-pages-articles-multistream.xml.bz2'
WIKIPEDIA_INDEX_DOWNLOAD_URL = 'https://dumps.wikimedia.org/enwiki/$(WIKI_DUMP_DATE)/enwiki-$(WIKI_DUMP_DATE)-pages-articles-multistream-index.txt.bz2'
WIKIPEDIA_DOWNLOAD_DIRECTORY = '$(LOCAL_DATA_DIRECTORY)/wikipedia/$(WIKI_DUMP_DATE)/'


.make/build-image:
	echo "Building Docker Image ..."
	docker build --build-arg WORKING_DIRECTORY=$(DOCKER_WORKING_DIRECTORY) --no-cache -t $(DOCKER_IMAGE_NAME) .
	touch $@

.PHONY: rebuild-image
rebuild-image:
	$(MAKE) -B .make/build-image

.PHONY: setup_project
setup_project:
	mkdir -p $(WIKIPEDIA_DOWNLOAD_DIRECTORY)
	mkdir -p .make
	$(MAKE) .make/build-image

define run_command
	## ----------------------------------------------------------------
	## This function runs commands inside docker
	## If docker container is detected, it runs the command as it is
	## If docker container is not detected, it runs the command inside docker
	## A docker image is built if not found
	## ----------------------------------------------------------------
	if [[ "${INSIDE_DOCKER}" == "" ]]; then \
		$(MAKE) .make/build-image ;\
		docker run -e DATA_DIRECTORY=$(DATA_DIRECTORY) --rm -it --name $(DOCKER_CONTAINER_NAME) \
		--mount type=bind,source=$(DATA_DIRECTORY),target=$(DATA_DIRECTORY) \
		--mount type=bind,source=$(CURDIR),target=$(DOCKER_WORKING_DIRECTORY) \
		$(DOCKER_IMAGE_NAME) ${1} ;\
	else \
		${1} ;\
	fi
endef

.PHONY: enter-docker-image
enter-docker-image: .make/build-image
	@$(call run_command, bash)

.PHONY: download_wikipedia
download_wikipedia:
	wget --continue --directory-prefix=$(WIKIPEDIA_DOWNLOAD_DIRECTORY) $(WIKIPEDIA_DOWNLOAD_URL)
	wget --continue --directory-prefix=$(WIKIPEDIA_DOWNLOAD_DIRECTORY) $(WIKIPEDIA_INDEX_DOWNLOAD_URL)

.PHONY: tests/unit
tests/unit:
	@echo "Running unit tests ..."
	@$(call run_command, poetry run pytest tests/unit)

.PHONY: tests/coverage-report
tests/coverage-report:
	@echo "Getting test coverage report ..."
	@$(call run_command, poetry run coverage run -m pytest && poetry run coverage html -d $(TEST_COVERAGE_REPORT_DIRECTORY) src/**.py)
	
.PHONY: format
format: 
	poetry run black .
	poetry run isort .