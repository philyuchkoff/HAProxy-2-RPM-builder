# RPM builder for latest HAProxy 2.3 (CentOS 7) with default syslog

![GitHub last commit](https://img.shields.io/github/last-commit/philyuchkoff/HAProxy-2-RPM-builder?style=for-the-badge)
![GitHub All Releases](https://img.shields.io/github/downloads/philyuchkoff/HAProxy-2-RPM-builder/total?style=for-the-badge)


## [HAProxy](http://www.haproxy.org/)

Perform the following steps on a build box as a regular user:


    sudo yum -y groupinstall 'Development Tools'
    cd /opt
    sudo git clone https://github.com/philyuchkoff/HAProxy-2-RPM-builder.git
    cd ./HAProxy-2-RPM-builder

## Build:

### Without Lua:

    sudo make
    
### With Lua:

    sudo make USE_LUA=1

### With Prometheus module:

    sudo make USE_PROMETHEUS=1

### Without sudo for YUM:

    sudo make NO_SUDO=1

Resulting RPM will be stored in 

    /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64/

## Build using Docker:

    sudo make run-docker

Resulting RPM will be stored in 

    ./RPMS/


### Install RPM:

    sudo yum -y install /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64/haproxy-2.3.7-1.el7.x86_64.rpm

or, if you build *.rpm with Docker:

    sudo yum -y install RPMS/haproxy-2.3.7-1.el7.x86_64.rpm 
    

## Check after install:

    haproxy -v

Must be like this:

    HA-Proxy version 2.3.7-2d39ce3 2021/03/16
    

## :exclamation: If some not working:

Check SELINUX:

    sestatus

If SELINUX is enabled  - switch off this: open /etc/selinux/config and change SELINUX to disabled:

    sudo sed -i s/^SELINUX=.*$/SELINUX=disabled/ /etc/selinux/config

## Stats page

After installation you can access a stats page **without** authenticating via the URL: `http://<YourHAProxyServer>:9000/haproxy_stats`
