.PHONY: install test load validate qa clean

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest tests/ -v

load:
	python -m src.etl.db_loader

qa:
	echo "QA steps"

clean:
	rm -rf __pycache__ .pytest_cache
