clean:
	find . -name \*.pyc -delete

restart:
	sudo systemctl restart pgo

purge:
	sudo echo 'flush_all' | nc localhost 11211
	sudo systemctl restart pgo
	sudo systemctl restart nginx
	sudo systemctl restart memcached
