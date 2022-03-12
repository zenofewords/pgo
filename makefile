clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete

restart:
	sudo systemctl restart pgo

flush:
	echo "flush_all" | nc -w 2 localhost 11211

purge:
	echo 'flush_all' | nc -w 2 localhost 11211
	sudo systemctl restart pgo
	sudo systemctl restart nginx
	sudo systemctl restart memcached

deploy:
	git pull origin master
	pip install --upgrade -r requirements.txt
	./manage.py migrate
	./manage.py collectstatic
	yarn install
	yarn build
	make restart
