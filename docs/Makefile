
api-docs: ../aparse/*
	PYTHONPATH=../ pdocs as_markdown -e -ov -o api aparse
	echo -e "---\nlayout: default\ntitle: API\nnav_order: 5\nhas_children: true\npermalink: /api\n---\n$$(cat api/aparse/index.md)" >api/aparse.md
	sed -i 's/\[aparse\.argparse\](argparse\/)/aparse.argparse/g' api/aparse.md
	sed -i 's/\[aparse\.core\](core\/)/aparse.core/g' api/aparse.md
	sed -i 's/\[aparse\.utils\](utils\/)/[aparse.utils](utils.html)/g' api/aparse.md
	sed -i 's/\[aparse\.click\](click\/)/[aparse.click](click.html)/g' api/aparse.md
	echo -e "---\nlayout: default\ntitle: aparse.click\nparent: API\n---\n$$(cat api/aparse/click.md)" >api/click.md
	echo -e "---\nlayout: default\ntitle: aparse.utils\nparent: API\n---\n$$(cat api/aparse/utils.md)" >api/utils.md
	rm -rf api/aparse

