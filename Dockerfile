FROM centos:7

RUN yum install -y wget && yum -y groupinstall 'Development Tools'
RUN mkdir RPMS
RUN chmod -R 777 RPMS
RUN mkdir SPECS
RUN mkdir SOURCES
COPY Makefile Makefile
COPY SPECS/haproxy.spec SPECS/haproxy.spec
COPY SOURCES/* SOURCES/

CMD make NO_SUDO=1 && cp /rpmbuild/RPMS/x86_64/* /RPMS && cp /rpmbuild/SRPMS/* /RPMS
