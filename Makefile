
all:

wwwroot:
	jupyter nbconvert ./tools/MakeWeb.ipynb --to python --output mweb.py
	cd tools && python3 mweb.py



