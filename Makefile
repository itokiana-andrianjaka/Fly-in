C_RESET		= \033[0m
C_GREEN		= \033[032m
C_BLUE		= \033[034m

RM = rm -rf
MYPY_FLAGS = \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

install:
	@echo "${C_BLUE}Installing dependencies...\n${C_RESET}"
	@uv sync

run:
	@uv run main.py $(MAP)

visual:
	@uv run main.py $(MAP) visual

text_output:
	@uv run main.py $(MAP) text_output

debug: install
	@.venv/bin/python -m pdb main.py $(MAPS)

clean:
	@echo "${C_BLUE}Removing temporary files or caches...\n${C_RESET}"
	@find . -type d -name "__pycache__" -exec $(RM) {} +
	@find . -type d -name ".mypy_cache" -exec $(RM) {} +
	@echo "${C_GREEN}Our project environment is clean\n${C_RESET}"

lint:
	@echo "${C_BLUE}Running flake8...\n${C_RESET}"
	@uv run flake8 . --exclude=.venv
	@echo "${C_BLUE}Running mypy with custom flags...\n${C_RESET}"
	@uv run mypy . $(MYPY_FLAGS)

lint-strict:
	@echo "${C_BLUE}Running flake8...\n${C_RESET}"
	@uv run flake8 . --exclude=.venv
	@echo "${C_BLUE}Running mypy --strict...\n${C_RESET}"
	@uv run mypy --strict .

.PHONY: install run visual text_output debug clean lint lint-strict
