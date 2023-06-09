
all:

wwwroot:
	jupyter nbconvert ./tools/MakeWebNew.ipynb --to python --output mweb.py
	cd tools && python3 mweb.py



