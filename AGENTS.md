# AGENTS Instructions

This project contains a chess engine written in Python. Follow these rules when contributing or automating changes.

## Style Guidelines

- **Python:** Adhere to [PEP 8](https://peps.python.org/pep-0008/). Use `classify-imports --apply` to keep imports grouped and sorted.
- Use `flake8` with the configuration from `requirements.txt` to lint the code.
- Keep code comments where logic is non-trivial, especially in bitboard or search modules.

## Testing

- Run `pytest` from the repository root (`python-implementation/tests`) before committing.
- Continuous integration expects tests to pass on Python 3.13.

## Pull Requests

- Ensure CI checks pass (`flake8` and `pytest`).
- Summaries should reference any closed issues (e.g., `Closes #123`).
- Describe the changes succinctly.

