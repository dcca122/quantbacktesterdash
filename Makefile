fmt:
	black .
	ruff check --fix .

lint:
	ruff check .

typecheck:
	mypy .

test:
	pytest
