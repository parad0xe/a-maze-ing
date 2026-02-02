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
PYTHON := $(VENV)/bin/python3
FLAKE8 := $(PYTHON) -m flake8 $(EXCLUDE)
MYPY := $(PYTHON) -m mypy $(EXCLUDE)
PIP := $(PYTHON) -m pip
POETRY := POETRY_VIRTUALENVS_IN_PROJECT=true $(PYTHON) -m poetry

PYTHONPATH := srcs

# rules
install: pyproject.toml $(WHEEL) | $(PYTHON)
	$(POETRY) install --no-root

run: install
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) $(MAIN) $(ARGS)

wheel: $(WHEEL)

clean:
	rm -rf $(PYCACHES) $(MYPYCACHES)
	rm -rf $(VENV)
	rm -f poetry.lock
	rm -rf $(WHEEL_DEST_DIR)

debug: install
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pdb $(MAIN) $(ARGS)

lint: install
	@PYTHONPATH=$(PYTHONPATH) $(FLAKE8)
	@PYTHONPATH=$(PYTHONPATH) $(MYPY) . --check-untyped-defs \
	--warn-unused-ignores --ignore-missing-imports \
	--warn-return-any --disallow-untyped-defs

lint-strict: install
	@PYTHONPATH=$(PYTHONPATH) $(FLAKE8)
	@PYTHONPATH=$(PYTHONPATH) $(MYPY) . --strict

$(PYTHON):
	@python3 -m venv $(VENV)
	@$(PIP) install -U pip
	@$(PIP) install -U poetry

$(WHEEL): $(WHEEL_FILES) | $(PYTHON)
	@$(POETRY) build -f wheel
	@$(PIP) install --no-deps --force-reinstall $(WHEEL)

# miscellaneous
.PHONY: install run debug lint lint-strict clean
