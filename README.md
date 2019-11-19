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

## С удовольствием приму все замечания
