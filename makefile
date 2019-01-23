.PHONY: deploy

quantum-freeze: *.py resources/*
	docker build -t qf .
	docker create -ti --name dummy qf bash
	docker cp dummy:/game/dist/quantum-freeze quantum-freeze
	docker rm -fv dummy


deploy: quantum-freeze
	scp quantum-freeze forest@64.84.57.28:quantum-freeze

conda-deploy: quantum-freeze
	conda build conda-build-qf
	echo "now run anaconda upload -u riverlane FILE_PRINTED_ABOVE"
