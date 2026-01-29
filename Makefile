# files
DIRS := . maze
MAIN := a_maze_ing.py
ARGS ?= config.txt
VENV := .venv

PYCACHES = $(addsuffix /__pycache__,$(DIRS))
MYPYCACHES = $(addsuffix /.mypy_cache,$(DIRS))

# tools
MAKEFLAGS += -j $$(nproc)
PYTHON := $(VENV)/bin/python3
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy
PIP := $(PYTHON) -m pip
POETRY := POETRY_VIRTUALENVS_IN_PROJECT=true poetry

# user rules
install: pyproject.toml $(PYTHON)
	$(POETRY) install

run: install
	$(PYTHON) $(MAIN) $(ARGS)

debug: install
	$(PYTHON) -m pdb $(MAIN) $(ARGS)

lint: install
	$(FLAKE8)
	$(MYPY) . --warn-return-any --warn-unused-ignores --check-untyped-defs \
		--ignore-missing-imports --disallow-untyped-defs 

lint-strict: install
	$(FLAKE8)
	$(MYPY) . --strict

clean:
	rm -rf $(PYCACHES) $(MYPYCACHES)

clean-venv:
	rm -rf $(VENV)
	rm poetry.lock

# build rule
$(PYTHON):
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -U poetry

# miscellaneous
.PHONY: install run debug lint lint-strict clean clean-venv
