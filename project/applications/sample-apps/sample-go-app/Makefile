# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
GOBIN=$(GOPATH)/bin
APP_DIR_LIST=$(shell go list ./... | grep -v /vendor/)

build: verify_gopath
	CGO_ENABLED=0 go install -tags netgo $(APP_DIR_LIST)
	go fmt $(APP_DIR_LIST)
	cp $(GOPATH)/bin/sample-go-app ./application/main

verify_gopath:
	@if [ -z "$(GOPATH)" ] || [ "$(GOPATH)" = "" ]; then\
		echo "GOPATH not set. You need to set GOPATH before run this command";\
		exit 1 ;\
	fi

deps_fetch_specific: bin/govendor
	@if [ "$(DEP_URL)" = "" ]; then\
		echo "DEP_URL not set. Run this comand as follow:";\
		echo " make deps_fetch_specific DEP_URL=github.com/nu7hatch/gouuid";\
	exit 1 ;\
	fi
	@echo "Fetching specific dependency in newest versions"
	$(GOBIN)/govendor fetch -v $(DEP_URL)

deps_update_tap: verify_gopath
	$(GOBIN)/govendor update github.com/trustedanalytics/...
	rm -Rf vendor/github.com/trustedanalytics/platform-tests/project/applications/sample-apps/sample-go-app
	@echo "Done"

bin/govendor: verify_gopath
	go get -v -u github.com/kardianos/govendor

test: verify_gopath
	go test --cover $(APP_DIR_LIST)

prepare_temp:
	mkdir -p temp/src/github.com/trustedanalytics/platform-tests/project/applications/sample-apps/sample-go-app
	$(eval REPOFILES=$(shell pwd)/*)
	ln -sf $(REPOFILES) temp/src/github.com/trustedanalytics/platform-tests/project/applications/sample-apps/sample-go-app
	mkdir -p application

clear_temp:
	rm -Rf ./temp

build_anywhere:
	$(MAKE) build_anywhere_linux
	$(MAKE) build_anywhere_win32
	$(MAKE) build_anywhere_osx

build_anywhere_linux:
	$(MAKE) build_anywhere_linux64
	$(MAKE) build_anywhere_linux32

build_anywhere_linux64:
	$(call prepare_env_for_build_app,linux,amd64,main-linux64)
	$(MAKE) build_app
	ln -sf main-linux64 application/main

build_anywhere_linux32:
	$(call prepare_env_for_build_app,linux,386,main-linux32)
	$(MAKE) build_app

build_anywhere_win32:
	$(call prepare_env_for_build_app,windows,386,main-windows32.exe)
	$(MAKE) build_app

build_anywhere_osx:
	$(call prepare_env_for_build_app,darwin,amd64,main-macosx64.osx)
	$(MAKE) build_app

build_app: prepare_temp
	$(eval GOPATH=$(shell readlink -f temp))
	$(eval APP_DIR_LIST=$(shell GOPATH=$(GOPATH) go list ./temp/src/github.com/trustedanalytics/platform-tests/project/applications/sample-apps/sample-go-app/... | grep -v /vendor/))
	GOPATH=$(GOPATH) CGO_ENABLED=0 GOOS=$(GOOS) GOARCH=$(GOARCH) go build -o ./application/$(OUTFILE) -tags netgo $(APP_DIR_LIST)
	$(MAKE) clear_temp

define prepare_env_for_build_app
	$(eval export GOOS=$(1))
	$(eval export GOARCH=$(2))
	$(eval export OUTFILE=$(3))
endef
