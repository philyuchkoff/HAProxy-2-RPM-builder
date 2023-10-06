# RPM builder for HAProxy 2.8 LTS (CentOS/RHEL 6/7/8/9)
## Build latest HAProxy binary with prometheus metrics support

![GitHub last commit](https://img.shields.io/github/last-commit/philyuchkoff/HAProxy-2-RPM-builder?style=for-the-badge)
![GitHub All Releases](https://img.shields.io/github/downloads/philyuchkoff/HAProxy-2-RPM-builder/total?style=for-the-badge)


### [HAProxy](http://www.haproxy.org/) 2.8.3 2023/09/07

Perform the following steps on a build box as a regular user:

#### CentOS7

    sudo yum -y groupinstall 'Development Tools'
    cd /opt
    sudo git clone https://github.com/philyuchkoff/HAProxy-2-RPM-builder.git
    cd ./HAProxy-2-RPM-builder
    
#### CentOS8

    sudo dnf -y groupinstall 'Development Tools'
    cd /opt
    sudo git clone https://github.com/philyuchkoff/HAProxy-2-RPM-builder.git
    cd ./HAProxy-2-RPM-builder
    sudo sed -i 's/yum/dnf/' Makefile

### Build:

#### Without Lua:

    sudo make
    
#### With Lua:

    sudo make USE_LUA=1

#### With Prometheus module:

    sudo make USE_PROMETHEUS=1

#### Without sudo for YUM:

    sudo make NO_SUDO=1

Resulting RPM will be stored in 

    /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64/

#### Build using Docker:

    sudo make run-docker

Resulting RPM will be stored in 

    ./RPMS/


### Install (for CentOS8/9 replaсe `yum` to `dnf`):

    sudo yum -y install /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64/haproxy-2.8.3-1.el7.x86_64.rpm

or, if you build *.rpm with Docker:

    sudo yum -y install RPMS/haproxy-2.8.3-1.el7.x86_64.rpm 
    

### Check after install:

    haproxy -v

### Stats page

After installation you can access a stats page **without** authenticating via the URL: `http://<YourHAProxyServer>:9000/haproxy_stats`



### Common problem:

#### :o: If some not working - check SELINUX:

    sestatus

If SELINUX is enabled  - switch off this: open /etc/selinux/config and change SELINUX to disabled:

    sudo sed -i s/^SELINUX=.*$/SELINUX=disabled/ /etc/selinux/config


#### :o: Cannot chroot1
    [/usr/sbin/haproxy.main()] Cannot chroot1(/var/lib/haproxy)  
##### Solution:
- Create `/var/lib/haproxy` directory
- Check on the rpcbind service to ensure that this service is started 

#### :o: Failed to download metadata for repo ‘AppStream’ (CentOS8/9)
##### Solution:
    cd /etc/yum.repos.d/
    sudo sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
    sudo sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
