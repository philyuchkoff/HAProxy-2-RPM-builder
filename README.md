Это черновик ридми, потом дооформляю :)

# Сборка RPM HAProxy самой свежей версии из ветки 2.0 CentOS7

Для сборки пакета выполните следующие действия под обычным пользователем:

## Установка необходимого для сборки  RPM

    sudo yum groupinstall 'Development Tools'

    cd /opt
    git clone https://github.com/philyuchkoff/HAProxy-2-RPM-builder.git
    cd ./HAProxy-2-RPM-builder
    git checkout master

    make
    
Собранный RPM будет лежать в 

    /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64
    
## Проверка

После установки пакета можно проверить:

    haproxy -v
    HA-Proxy version 2.0.9 2019/11/15 - https://haproxy.org/
    
## Если что-то не работает
То первым делом проверьте

    sestatus
    
Если он в enabled - отключите: откройте /etc/selinux/config и установите SELINUX в disabled

    

## С удовольствием приму все замечания
