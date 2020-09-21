FROM centos:7

RUN yum install -y wget pcre-devel make gcc openssl-devel rpm-build systemd-devel wget sed zlib-devel && \
mkdir RPMS && \
chmod -R 777 RPMS && \
mkdir SPECS && \
mkdir SOURCES
COPY Makefile Makefile
COPY SPECS/haproxy.spec SPECS/haproxy.spec
COPY SOURCES/* SOURCES/

CMD make NO_SUDO=1 && cp /rpmbuild/RPMS/x86_64/* /RPMS && cp /rpmbuild/SRPMS/* /RPMS
