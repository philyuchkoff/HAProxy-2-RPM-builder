Это черновик ридми, потом дооформляю :)

# СборкаRPM HAProxy самой свежей версии из ветки 2.0 CentOS7

Для сборки пакета выполните следующие действия под обычным пользователем:

## Установка необходимого для сборки  RPM

    sudo yum groupinstall 'Development Tools'

## Склонируйте себе репозиторий

    cd /opt
    git clone https://github.com/philyuchkoff/HAProxy-2-RPM-builder.git
    cd ./HAProxy-2-RPM-builder
    git checkout 2.0

## Установите
    make
    
Собранный RPM будет лежать в /opt/rpm-haproxy/rpmbuild/RPMS/x86_64/

## С удовольствием приму все замечания
