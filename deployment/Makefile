# Makefile for python code
# 
# - $ python3 app.py     # Uses the system Python
# - $ ./venv/bin/python3 # USes the virtualenv Python
#
# - writing ./venv.bin/ every time can be time consuming, 
#	especially if you have to run a lot of commands that use
#	Python or pip. To overcome this, you can “activate” the 
#	virtual environment by running: $ ./venv/bin/activate
#
.PHONY: all

VENV_PATH='env/bin/activate'
ENVIRONMENT_VARIABLE_FILE='.env'

DOCKER_NAME:=$(DOCKER_0_NODE_NAME)
DOCKER_TAG:=$(DOCKER_0_NODE_TAG)
CONTEXT_PATH:=$(CONTEXT_PATH)
NODE_DOCKERFILE:=$(DOCKER_0_NODE_DOCKERFILE)


define find.functions
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
endef

help:
	@echo 'The following commands can be used.'
	@echo ''
	$(call find.functions)


init:
	@echo $(DOCKER_NAME)
	@echo $(DOCKER_TAG)
	@echo $(CONTEXT_PATH)
	@echo $(NODE_DOCKERFILE)
	pip install -r requirements.txt

install:
	python3 -m pip install --upgrade pip
	pip install setuptools wheel pytest

clean:
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	rm -rf .pytest_cache
	# Remove all pycache
	find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

env:
	python3 -m venv env
	source $(VENV_PATH)
	source $(ENVIRONMENT_VARIABLE_FILE)

leave: clean
	deactivate

test:
	pytest . -p no:logging -p no:warnings

build:
	docker build -t "$$DOCKER_NAME":"$$DOCKER_TAG" -f "$$NODE_DOCKERFILE" "$$CONTEXT_PATH" 

create: build
	docker create -it --name "$$DOCKER_NAME" "$$DOCKER_NAME":"$$DOCKER_TAG"

start: build
	docker start "$$DOCKER_NAME"

run: start
	docker run -it "$$DOCKER_NAME":"$$DOCKER_TAG"

exec: start
	docker exec -it "$$DOCKER_NAME" python