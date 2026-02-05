# structure
DIRS := . src mazegen
MAIN := a_maze_ing.py
ARGS ?= config.txt
VENV := .venv

POETRY_LOCK := poetry.lock
PYPROJECT_TOML := pyproject.toml

PYCACHES = $(addsuffix /__pycache__,$(DIRS))
MYPYCACHES = $(addsuffix /.mypy_cache,$(DIRS))
EXCLUDE = --exclude $(VENV)

# tools
PYTHON := $(VENV)/bin/python3
FLAKE8 := $(PYTHON) -m flake8 $(EXCLUDE)
MYPY := $(PYTHON) -m mypy $(EXCLUDE)
PIP := $(PYTHON) -m pip
POETRY := POETRY_VIRTUALENVS_IN_PROJECT=true $(PYTHON) -m poetry

WHEEL_NAME := mazegen
WHEEL_DIR := mazegen
WHEEL_VER := $(shell sed -n '/^version*=*/{s/.*"\(.*\)".*/\1/p;q}' \
			 $(PYPROJECT_TOML))
WHEEL_DEST_DIR := dist
WHEEL_FILES := $(WHEEL_DIR)/mazegen.py \
			   $(WHEEL_DIR)/__init__.py \
			   $(WHEEL_DIR)/py.typed \
			   $(WHEEL_DIR)/README.md
WHEEL := $(WHEEL_DEST_DIR)/$(WHEEL_NAME)-$(WHEEL_VER)-py3-none-any.whl

# rules
install: $(PYPROJECT_TOML) $(POETRY_LOCK) $(WHEEL) | $(PYTHON)
	$(POETRY) install --with dev --no-root

run: install
	@$(PYTHON) $(MAIN) $(ARGS)

wheel: $(WHEEL)

clean:
	rm -rf $(PYCACHES) $(MYPYCACHES)
	rm -rf $(VENV)
	rm -rf $(WHEEL_DEST_DIR)

debug: install
	@$(PYTHON) -m pdb $(MAIN) $(ARGS)

lint: install
	@$(FLAKE8)
	@$(MYPY) . --check-untyped-defs \
	--warn-unused-ignores --ignore-missing-imports \
	--warn-return-any --disallow-untyped-defs

lint-strict: install
	@$(FLAKE8)
	@$(MYPY) . --strict

$(PYTHON):
	@python3 -m venv $(VENV)
	@$(PIP) install -U pip
	@$(PIP) install -U poetry

$(WHEEL): $(WHEEL_FILES) | $(PYTHON)
	@$(POETRY) build -f wheel
	@$(PIP) install --no-deps --force-reinstall $(WHEEL)

$(POETRY_LOCK): $(PYPROJECT_TOML) | $(PYTHON)
	@$(POETRY) lock

# miscellaneous
.PHONY: install run debug lint lint-strict clean wheel
