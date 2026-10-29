PY ?= python

.PHONY: all download analysis build descriptives models strengths behavior export clean

all: download analysis

download:
	cd src && $(PY) 01_download.py

analysis: build descriptives models strengths behavior export

build:
	cd src && $(PY) 02_build_analytic.py

descriptives:
	cd src && $(PY) 03_descriptives.py

models:
	cd src && $(PY) 04_models.py

strengths:
	cd src && $(PY) 05_strengths.py

behavior:
	cd src && $(PY) 06_behavior_adjustment.py

export:
	cd src && $(PY) 07_export_data.py

clean:
	rm -rf data/processed/*.csv output/tables/*.csv output/figures/*.png output/*.md data/analytic/*
