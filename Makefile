SHELL=/bin/bash
DOCKERUSER=geunsam2
IMGNAME=confluence2tistory
VERSION=v1
IMGFULLNAME=$(DOCKERUSER)/$(IMGNAME):$(VERSION)
PORT=8000

build :
	docker build -t $(IMGFULLNAME) -f docker/Dockerfile .
	docker push $(IMGFULLNAME)

publish : build 
	echo '## Check Container live'
	if [ 1 -eq  $(shell docker ps | grep convconf | wc -l) ];then echo '## Remove Container'; docker stop convconf; sleep 2; fi
	echo '## Run New Container'
	docker run -dit -p $(PORT):443 -p 8001:8888 -v $(shell pwd):/app --rm --name convconf $(IMGFULLNAME)
