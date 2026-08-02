FROM rockylinux:9

RUN dnf groupinstall -y "Development Tools" \
 && dnf install -y openssl-devel zlib-devel systemd-rpm-macros pcre2-devel \
                   rpm-build redhat-rpm-config make gcc wget tar which \
 && dnf clean all

WORKDIR /build
COPY . /build

ENV USE_LUA=0 \
    USE_PROMETHEUS=0 \
    RELEASE=1

ENTRYPOINT ["/build/build.sh"]
