DOCKERUSER=geunsam2
IMGNAME=confluence2tistory
VERSION=v1

build :
	docker build -t $(DOCKERUSER)/$(IMGNAME):$(VERSION) -f docker/Dockerfile .
