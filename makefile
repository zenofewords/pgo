clean:
	find . -name \*.pyc -delete

restart:
	sudo echo 'flush_all' | nc localhost 11211
	sudo systemctl restart gunicorn
	sudo systemctl restart nginx
	sudo systemctl restart memcached
