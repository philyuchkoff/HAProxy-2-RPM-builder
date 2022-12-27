HOME=$(shell pwd)
MAINVERSION=2.7
LUA_VERSION=5.4.4
USE_LUA?=0
NO_SUDO?=0
USE_PROMETHEUS?=0
VERSION=$(shell wget -qO- https://git.haproxy.org/git/haproxy-${MAINVERSION}.git/refs/tags/ | sed -n 's:.*>\(.*\)</a>.*:\1:p' | sed 's/^.//' | sort -rV | head -1)
ifeq ("${VERSION}","./")
	VERSION="${MAINVERSION}.0"
endif
RELEASE=1

all: build

install_prereq:
ifeq ($(NO_SUDO),1)
	yum install -y pcre-devel make gcc openssl-devel rpm-build systemd-devel wget sed zlib-devel
else
	sudo yum install -y pcre-devel make gcc openssl-devel rpm-build systemd-devel wget sed zlib-devel
endif

clean:
ifeq ($(NO_SUDO),1)
	rm -f ./SOURCES/haproxy-${VERSION}.tar.gz
	rm -rf ./rpmbuild
	mkdir -p ./rpmbuild/SPECS/ ./rpmbuild/SOURCES/ ./rpmbuild/RPMS/ ./rpmbuild/SRPMS/
	rm -rf ./lua-${LUA_VERSION}*
else
	sudo rm -f ./SOURCES/haproxy-${VERSION}.tar.gz
	sudo rm -rf ./rpmbuild
	sudo mkdir -p ./rpmbuild/SPECS/ ./rpmbuild/SOURCES/ ./rpmbuild/RPMS/ ./rpmbuild/SRPMS/
	sudo rm -rf ./lua-${LUA_VERSION}*
endif

download-upstream:
ifeq ($(NO_SUDO),1)
	wget https://www.haproxy.org/download/${MAINVERSION}/src/haproxy-${VERSION}.tar.gz -O ./SOURCES/haproxy-${VERSION}.tar.gz
else
	sudo wget https://www.haproxy.org/download/${MAINVERSION}/src/haproxy-${VERSION}.tar.gz -O ./SOURCES/haproxy-${VERSION}.tar.gz
endif

build_lua:
ifeq ($(NO_SUDO),1)
	yum install -y readline-devel
	wget --no-check-certificate https://www.lua.org/ftp/lua-${LUA_VERSION}.tar.gz
	tar xzf lua-${LUA_VERSION}.tar.gz
	cd lua-${LUA_VERSION}
	$(MAKE) -C lua-${LUA_VERSION} clean
	$(MAKE) -C lua-${LUA_VERSION} MYCFLAGS=-fPIC linux test  # MYCFLAGS=-fPIC is required during linux ld
	$(MAKE) -C lua-${LUA_VERSION} install
else
	sudo yum install -y readline-devel
	sudo wget --no-check-certificate https://www.lua.org/ftp/lua-${LUA_VERSION}.tar.gz
	sudo tar xzf lua-${LUA_VERSION}.tar.gz
	cd lua-${LUA_VERSION}
	sudo $(MAKE) -C lua-${LUA_VERSION} clean
	sudo $(MAKE) -C lua-${LUA_VERSION} MYCFLAGS=-fPIC linux test  # MYCFLAGS=-fPIC is required during linux ld
	sudo $(MAKE) -C lua-${LUA_VERSION} install
endif

build_stages := install_prereq clean download-upstream
ifeq ($(USE_LUA),1)
	build_stages += build_lua
endif

build-docker:
	docker build -t haproxy-rpm-builder:latest -f Dockerfile .

run-docker: build-docker
	mkdir -p RPMS
	docker run --volume $(HOME)/RPMS:/RPMS --rm haproxy-rpm-builder:latest

build: $(build_stages)
ifeq ($(NO_SUDO),1)
	cp -r ./SPECS/* ./rpmbuild/SPECS/ || true
	cp -r ./SOURCES/* ./rpmbuild/SOURCES/ || true
	rpmbuild -ba SPECS/haproxy.spec \
	--define "mainversion ${MAINVERSION}" \
	--define "version ${VERSION}" \
	--define "release ${RELEASE}" \
	--define "_topdir %(pwd)/rpmbuild" \
	--define "_builddir %{_topdir}/BUILD" \
	--define "_buildroot %{_topdir}/BUILDROOT" \
	--define "_rpmdir %{_topdir}/RPMS" \
	--define "_srcrpmdir %{_topdir}/SRPMS" \
	--define "_use_lua ${USE_LUA}" \
	--define "_use_prometheus ${USE_PROMETHEUS}"
else
	sudo cp -r ./SPECS/* ./rpmbuild/SPECS/ || true
	sudo cp -r ./SOURCES/* ./rpmbuild/SOURCES/ || true
	sudo rpmbuild -ba SPECS/haproxy.spec \
	--define "mainversion ${MAINVERSION}" \
	--define "version ${VERSION}" \
	--define "release ${RELEASE}" \
	--define "_topdir %(pwd)/rpmbuild" \
	--define "_builddir %{_topdir}/BUILD" \
	--define "_buildroot %{_topdir}/BUILDROOT" \
	--define "_rpmdir %{_topdir}/RPMS" \
	--define "_srcrpmdir %{_topdir}/SRPMS" \
	--define "_use_lua ${USE_LUA}" \
	--define "_use_prometheus ${USE_PROMETHEUS}"
endif
