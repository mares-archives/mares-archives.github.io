install:
	git submodule update --remote --merge
	pip3 install -r requirements.txt
	npm install

generate:
	python3 maresarchives.py generate --compile-tailwind --verbose

serve:
	python3 maresarchives.py serve

serve-no-livereload:
	python3 maresarchives.py serve --no-livereload
