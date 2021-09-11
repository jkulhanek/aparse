
api-docs: ../aparse/*
	PYTHONPATH=../ pdocs as_markdown -e -ov -o api aparse
	echo -e "---\nlayout: default\ntitle: aparse\nnav_order: 1\npermalink: /api/aparse\n---\n$$(cat api/aparse/index.md)" >api/aparse.md
	echo -e "---\nlayout: default\ntitle: aparse.click\nnav_order: 2\npermalink: /api/aparse.click\n---\n$$(cat api/aparse/click.md)" >api/click.md
	rm -rf api/aparse

