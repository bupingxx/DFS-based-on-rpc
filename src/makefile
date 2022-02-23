db:
	python serverDB.py

s1:
	python server.py 1 8001
s2:
	python server.py 2 8002
s3:
	python server.py 3 8003

cr_Bob:
	python client.py register Bob 123

cl_Bob:
	python client.py login Bob 123

cr_Alice:
	python client.py register Alice 321

cl_Alice:
	python client.py login Alice 321

clean:
	rm serverDB.db