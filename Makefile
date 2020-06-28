# Useful commands:
#   make test    | Runs tests
#   make build   | Fetches packages
#   make version | Display version of the package (from chinese/_version.py)
#   make package | Builds everything, drops a new zip file in build/ dir


export PYTHONPATH=.
PYTHON3_VERSION=$(shell python3 -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)")
VERSION=`cat chinese/_version.py | grep __version__ | sed "s/.*'\(.*\)'.*/\1/"`
PYTEST=pytest

test:
	"$(PYTEST)" --cov=chinese tests -v

version:
	@ECHO $(VERSION)

package: build
	./package-for-anki.sh $(VERSION)

clean:
	rm -fr chinese/lib/
	rm -fr virtual_env/
	find . -name '*.pyc' -type f -delete
	find . -name .mypy_cache -type d -exec rm -rf {} +
	find . -name .ropeproject -type d -exec rm -rf {} +
	find . -name __pycache__ -type d -exec rm -rf {} +

build: clean venv/bin/activate
	rm -fr chinese/lib
	mkdir chinese/lib
	cp -R virtual_env/lib/python$(PYTHON3_VERSION)/site-packages/. chinese/lib/
	cp LICENSE "chinese/LICENSE.txt"
	git checkout chinese/data/db/chinese.db

venv/bin/activate: requirements-minimal.txt
	rm -rf virtual_env/
	python3 -m venv virtual_env
	. virtual_env/bin/activate ;\
	pip install --upgrade pip ;\
	pip install -Ur requirements-minimal.txt ;\
	pip freeze | sort > requirements.txt
	touch virtual_env/bin/activate  # update so it's as new as requirements-minimal.txt
