# structure
DIRS := . srcs mazegen
MAIN := a_maze_ing.py
ARGS ?= config.txt
VENV := .venv

WHEEL_NAME := mazegen
WHEEL_DIR := mazegen
WHEEL_VER := 0.0.1
WHEEL_DEST_DIR := dist
WHEEL_FILES := $(WHEEL_DIR)/mazegen.py $(WHEEL_DIR)/__init__.py
WHEEL := $(WHEEL_DEST_DIR)/$(WHEEL_NAME)-$(WHEEL_VER)-py3-none-any.whl
WHEEL_STAMP := $(VENV)/.mazegen_installed

PYCACHES = $(addsuffix /__pycache__,$(DIRS))
MYPYCACHES = $(addsuffix /.mypy_cache,$(DIRS))
EXCLUDE = --exclude $(VENV)

# tools
PYTHON := PYTHONPATH=srcs $(VENV)/bin/python3
FLAKE8 := $(PYTHON) -m flake8 $(EXCLUDE)
MYPY := $(PYTHON) -m mypy $(EXCLUDE)
PIP := $(PYTHON) -m pip
POETRY := POETRY_VIRTUALENVS_IN_PROJECT=true $(PYTHON) -m poetry


# rules
install: pyproject.toml $(WHEEL) | $(PYTHON)
	$(POETRY) install --no-root

run: install
	@$(PYTHON) $(MAIN) $(ARGS)

wheel: $(WHEEL)

clean:
	rm -rf $(PYCACHES) $(MYPYCACHES)
	rm -rf $(VENV)
	rm -f poetry.lock
	rm -rf $(WHEEL_DEST_DIR)

debug: install
	$(PYTHON) -m pdb $(MAIN) $(ARGS)

lint: install
	@$(FLAKE8)
	@$(MYPY) . --warn-return-any --warn-unused-ignores --check-untyped-defs \
		--ignore-missing-imports --disallow-untyped-defs 

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

# miscellaneous
.PHONY: install run debug lint lint-strict clean
