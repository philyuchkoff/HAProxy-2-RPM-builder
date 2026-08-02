%define haproxy_user    haproxy
%define haproxy_group   %{haproxy_user}
%define haproxy_home    %{_localstatedir}/lib/haproxy

%if 0%{?rhel} > 6 && 0%{!?amzn2}
    %define dist %{expand:%%(/usr/lib/rpm/redhat/dist.sh --dist)}
%endif

%if 0%{?rhel} < 7
    %{!?__global_ldflags: %global __global_ldflags -Wl,-z,relro}
%endif

%global _hardened_build 1

Summary: HA-Proxy reverse proxy for high availability environments
Name: haproxy
Version: %{version}
Release: %{release}%{?dist}
License: GPLv2+
Group: System Environment/Daemons
URL: http://www.haproxy.org/
Source0: http://www.haproxy.org/download/%{mainversion}/src/%{name}-%{version}.tar.gz
Source1: %{name}.cfg
%if 0%{?el6} || 0%{?amzn1}
Source2: %{name}.init
%else
Source2: %{name}.service
%endif
Source3: %{name}.logrotate
Source4: %{name}.syslog%{?dist}
Source5: halog.1

# Ready-to-use config recipes, one file per README example. They ship under
# /usr/share/haproxy rather than as %%doc so `rpm --excludedocs` can't strip
# them: they are templates users copy from, not reading material.
Source10: README.txt
Source11: check-example.sh
Source20: 00-base.cfg
Source21: 01-web-http-lb.cfg
Source22: 02-real-client-ip.cfg
Source23: 03-https-offload.cfg
Source24: 04-http2.cfg
Source25: 05-routing-acl.cfg
Source26: 06-sticky-session.cfg
Source27: 07-mysql.cfg
Source28: 08-mysql-rw-split.cfg
Source29: 09-postgresql.cfg
Source30: 10-redis.cfg
Source31: 11-tcp-passthrough.cfg
Source32: 12-rate-limit.cfg
Source33: 13-maintenance.cfg

BuildRoot: %{_tmppath}/%{name}-%{version}-root

# PCRE2, not PCRE1: HAProxy 3 recommends it and PCRE1 has been end-of-life
# upstream since 2020.
BuildRequires: pcre2-devel
BuildRequires: zlib-devel
BuildRequires: make
BuildRequires: gcc openssl-devel
BuildRequires: openssl-devel

Requires(pre):      shadow-utils
Requires:           rsyslog

%if 0%{?el6} || 0%{?amzn1}
Requires(post):     chkconfig, initscripts
Requires(preun):    chkconfig, initscripts
Requires(postun):   initscripts
%endif

%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
# Only the rpm macros (%%{_unitdir}, %%systemd_post, ...) are needed. HAProxy 3
# implements sd_notify itself, so it no longer links against libsystemd and
# systemd-devel has nothing left to contribute.
BuildRequires:      systemd-rpm-macros
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%endif

%description
HA-Proxy is a TCP/HTTP reverse proxy which is particularly suited for high
availability environments. Indeed, it can:
- route HTTP requests depending on statically assigned cookies
- spread the load among several servers while assuring server persistence
  through the use of HTTP cookies
- switch to backup servers in the event a main one fails
- accept connections to special ports dedicated to service monitoring
- stop accepting connections without breaking existing ones
- add/modify/delete HTTP headers both ways
- block requests matching a particular pattern

It needs very little resource. Its event-driven architecture allows it to easily
handle thousands of simultaneous connections on hundreds of instances without
risking the system's stability.

# This spec started life in philyuchkoff's HAProxy-2-RPM-builder. That project
# targets the 2.x series, which this package no longer builds, so the pointer
# is kept here as attribution rather than in the user-visible description.

%prep
%setup -q

# We don't want any perl dependecies in this RPM:
%define __perl_requires /bin/true

%build
RPM_BUILD_NCPUS="`/usr/bin/nproc 2>/dev/null || /usr/bin/getconf _NPROCESSORS_ONLN`";

# Three options this spec used to pass are gone from HAProxy 3, which reports
# them as "ignoring unknown build option" and carries on:
#   USE_REGPARM   dropped upstream; it only ever helped 32-bit x86.
#   USE_SYSTEMD   sd_notify is built in now, with no libsystemd to link.
#   CPU=generic   the CPU variable is no longer used; per-CPU tuning belongs
#                 in CPU_CFLAGS.
# USE_TFO and USE_NS are unconditional here because the linux-glibc target
# enables both by default. The old per-distro branches left them empty on
# anything unrecognised, which overrode that default and switched them off.
pcre_opts="USE_PCRE2=1 USE_PCRE2_JIT=1"

%if 0%{_use_lua}
SET_LUA="USE_LUA=1"
%endif

%if 0%{_use_prometheus}
SET_PROMETHEUS="USE_PROMEX=1"
%endif

%{__make} -j$RPM_BUILD_NCPUS %{?_smp_mflags} TARGET="linux-glibc" ${pcre_opts} USE_OPENSSL=1 USE_ZLIB=1 ADDINC="%{optflags}" USE_LINUX_TPROXY=1 USE_THREAD=1 USE_TFO=1 USE_NS=1 ${SET_LUA} ${SET_PROMETHEUS} ADDLIB="%{__global_ldflags}"

%{__make} admin/halog/halog OPTIMIZE="%{optflags} %{__global_ldflags}"

pushd admin/iprange
%{__make} iprange OPTIMIZE="%{optflags} %{__global_ldflags}"
popd

%install
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}

%{__install} -d %{buildroot}%{_sbindir}
%{__install} -d %{buildroot}%{_bindir}
%{__install} -d %{buildroot}%{_sysconfdir}/%{name}
%{__install} -d %{buildroot}%{_sysconfdir}/%{name}/errors
%{__install} -d %{buildroot}%{_mandir}/man1/
%{__install} -d %{buildroot}%{_sysconfdir}/logrotate.d
%{__install} -d %{buildroot}%{_sysconfdir}/rsyslog.d
%{__install} -d %{buildroot}%{_localstatedir}/log/%{name}
%{__install} -d %{buildroot}%{haproxy_home}
%{__install} -d %{buildroot}%{_datadir}/%{name}/examples

%{__install} -s %{name} %{buildroot}%{_sbindir}/


%{__install} -c -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/%{name}/haproxy.cfg
%{__install} -c -m 644 examples/errorfiles/*.http %{buildroot}%{_sysconfdir}/%{name}/errors/
%{__install} -c -m 644 doc/%{name}.1 %{buildroot}%{_mandir}/man1/
%{__install} -c -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/rsyslog.d/49-%{name}.conf
%{__install} -c -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

%define example_dir %{buildroot}%{_datadir}/%{name}/examples
%{__install} -c -m 644 %{SOURCE10} %{example_dir}/README.txt
%{__install} -c -m 755 %{SOURCE11} %{example_dir}/check-example.sh
%{__install} -c -m 644 %{SOURCE20} %{example_dir}/00-base.cfg
%{__install} -c -m 644 %{SOURCE21} %{example_dir}/01-web-http-lb.cfg
%{__install} -c -m 644 %{SOURCE22} %{example_dir}/02-real-client-ip.cfg
%{__install} -c -m 644 %{SOURCE23} %{example_dir}/03-https-offload.cfg
%{__install} -c -m 644 %{SOURCE24} %{example_dir}/04-http2.cfg
%{__install} -c -m 644 %{SOURCE25} %{example_dir}/05-routing-acl.cfg
%{__install} -c -m 644 %{SOURCE26} %{example_dir}/06-sticky-session.cfg
%{__install} -c -m 644 %{SOURCE27} %{example_dir}/07-mysql.cfg
%{__install} -c -m 644 %{SOURCE28} %{example_dir}/08-mysql-rw-split.cfg
%{__install} -c -m 644 %{SOURCE29} %{example_dir}/09-postgresql.cfg
%{__install} -c -m 644 %{SOURCE30} %{example_dir}/10-redis.cfg
%{__install} -c -m 644 %{SOURCE31} %{example_dir}/11-tcp-passthrough.cfg
%{__install} -c -m 644 %{SOURCE32} %{example_dir}/12-rate-limit.cfg
%{__install} -c -m 644 %{SOURCE33} %{example_dir}/13-maintenance.cfg

%{__install} -p -m 0755 ./admin/halog/halog %{buildroot}%{_bindir}/halog
%{__install} -p -m 0755 ./admin/iprange/iprange %{buildroot}%{_bindir}/iprange
%{__install} -p -D -m 0644 %{SOURCE5} %{buildroot}%{_mandir}/man1/halog.1

%if 0%{?el6} || 0%{?amzn1}
%{__install} -d %{buildroot}%{_sysconfdir}/rc.d/init.d
%{__install} -c -m 755 %{SOURCE2} %{buildroot}%{_sysconfdir}/rc.d/init.d/%{name}
%endif

%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
%{__install} -s %{name} %{buildroot}%{_sbindir}/
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}.service
%endif

%clean
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}

%pre
getent group %{haproxy_group} >/dev/null || \
       groupadd -g 188 -r %{haproxy_group}
getent passwd %{haproxy_user} >/dev/null || \
       useradd -u 188 -r -g %{haproxy_group} -d %{haproxy_home} \
       -s /sbin/nologin -c "%{name}" %{haproxy_user}
exit 0

%post
%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
%systemd_post %{name}.service
systemctl reload-or-try-restart rsyslog.service
%endif

%if 0%{?el6} || 0%{?amzn1}
/sbin/chkconfig --add %{name}
/sbin/service rsyslog restart >/dev/null 2>&1 || :
%endif

%preun
%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
%systemd_preun %{name}.service
%endif

%if 0%{?el6} || 0%{?amzn1}
if [ $1 = 0 ]; then
  /sbin/service %{name} stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del %{name}
fi
%endif

%postun
%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
%systemd_postun_with_restart %{name}.service
systemctl reload-or-try-restart rsyslog.service
%endif

%if 0%{?el6} || 0%{?amzn1}
if [ "$1" -ge "1" ]; then
  /sbin/service %{name} condrestart >/dev/null 2>&1 || :
  /sbin/service rsyslog restart >/dev/null 2>&1 || :
fi
%endif

%files
%defattr(-,root,root)
%doc CHANGELOG examples/*.cfg doc/configuration.txt doc/intro.txt doc/management.txt doc/proxy-protocol.txt
%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
    %license LICENSE
%endif
%doc %{_mandir}/man1/*
%dir %{_sysconfdir}/%{name}
%{_sysconfdir}/%{name}/errors
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.cfg
%attr(0755,root,root) %{_sbindir}/%{name}
# Config recipes. Deliberately not %config: they are pristine templates, so an
# upgrade should always replace them with the current versions.
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/examples
%dir %{_localstatedir}/log/%{name}
%dir %attr(0755,%{haproxy_user},%{haproxy_group}) %{haproxy_home}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/rsyslog.d/49-%{name}.conf
%{_bindir}/halog
%{_bindir}/iprange

%if 0%{?el6} || 0%{?amzn1}
%attr(0755,root,root) %config %_sysconfdir/rc.d/init.d/%{name}
%endif

%if 0%{?el7} || 0%{?amzn2} || 0%{?el8} || 0%{?el9}
%attr(-,root,root) %{_unitdir}/%{name}.service
%endif
