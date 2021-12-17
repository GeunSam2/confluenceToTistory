SHELL=/bin/bash
DOCKERUSER=geunsam2
IMGNAME=confluence2tistory
CONTAINERNAME=convconf
VERSION=v1
IMGFULLNAME=$(DOCKERUSER)/$(IMGNAME):$(VERSION)
PORT=8000

build :
	docker build -t $(IMGFULLNAME) -f docker/Dockerfile .
	docker push $(IMGFULLNAME)

publish : build 
	echo '## Check Container live'
	if [ 1 -eq  $(shell docker ps | grep $(CONTAINERNAME) | wc -l) ];then echo '## Remove Container'; docker stop $(CONTAINERNAME); sleep 2; fi
	echo '## Run New Container'
	docker run -dit -p $(PORT):80 -v $(shell pwd):/app --rm --name $(CONTAINERNAME) $(IMGFULLNAME)
