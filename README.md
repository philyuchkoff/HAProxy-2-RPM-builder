Это черновик ридми, потом дооформляю :)

# СборкаRPM HAProxy самой свежей версии из ветки 2.0 CentOS7

Для сборки пакета выполните следующие действия под обычным пользователем:

## Установка необходимого для сборки  RPM

    sudo yum groupinstall 'Development Tools'

## Склонируйте себе репозиторий

    cd /opt
    git clone https://github.com/philyuchkoff/haproxy-1.9-RPM-builder.git
    cd ./rpm-haproxy
    git checkout 1.9

## Установите
    make
    
Собранный RPM будет лежать в /opt/rpm-haproxy/rpmbuild/RPMS/x86_64/

## С удовольствием приму все замечания
