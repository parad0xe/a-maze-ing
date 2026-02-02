# files
DIRS := . maze
MAIN := a_maze_ing.py
ARGS ?= config.txt
VENV := .venv

PYCACHES = $(addsuffix /__pycache__,$(DIRS))
MYPYCACHES = $(addsuffix /.mypy_cache,$(DIRS))
EXCLUDE = --exclude $(VENV)

# tools
PYTHON := $(VENV)/bin/python3
FLAKE8 := $(PYTHON) -m flake8 $(EXCLUDE)
MYPY := $(PYTHON) -m mypy $(EXCLUDE)
PIP := $(PYTHON) -m pip
POETRY := POETRY_VIRTUALENVS_IN_PROJECT=true $(PYTHON) -m poetry

# user rules
install: pyproject.toml $(PYTHON)
	$(POETRY) build -f wheel
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
	rm -f poetry.lock

clean-wheel:
	rm -rf dist

clean-all: clean clean-venv clean-wheel

# build rule
$(PYTHON):
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -U poetry

# miscellaneous
.PHONY: install run debug lint lint-strict clean clean-venv
