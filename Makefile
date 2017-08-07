all: init tests

tests: test-quality test-readme test

init:
	pip3 install -r requirements.txt

test-quality:
	flake8 --max-line-length=100 pyhomekit
	pylint --disable=C0103,C0111,C0326,C0330,W0232,W0251,W0511,R0902,R0903,R0904,R0913,R0914,E0401 pyhomekit
	mypy --ignore-missing-imports --strict-optional --disallow-untyped-defs --show-column-numbers pyhomekit

test-readme:
	python3 setup.py check --restructuredtext --strict && ([ $$? -eq 0 ] && echo "README.rst and HISTORY.rst ok") || echo "Invalid markup in README.rst or HISTORY.rst!"

test:
	py.test

doc:
	rm -rf ./docs/_*
	cd docs && sphinx-apidoc -o source/ ../pyhomekit/
	cd docs && make html

.PHONY: all init test-quality test-readme test