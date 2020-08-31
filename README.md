# Сборка RPM HAProxy самой свежей версии из ветки 2.1 (для CentOS 7)
### :new: Latest HAProxy 2.2 rpm for CentOS 7 here: https://github.com/philyuchkoff/HAProxy-2-RPM-builder/releases/tag/2.2

Для сборки пакета выполните следующие действия под обычным пользователем:

## Установка:

    sudo yum groupinstall 'Development Tools'
    cd /opt
    sudo git clone https://github.com/philyuchkoff/HAProxy-2-RPM-builder.git
    cd ./HAProxy-2-RPM-builder
    sudo git checkout master
    sudo make
    
Собранный RPM (--------) будет лежать в 

    /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64/haproxy-2.1.8-1.el7.x86_64.rpm

### Установить пакет

    sudo yum -y install /opt/HAProxy-2-RPM-builder/rpmbuild/RPMS/x86_64/haproxy-2.1.8-1.el7.x86_64.rpm
    
## Проверка

После установки пакета можно проверить:

    haproxy -v

    HA-Proxy version 2.1.8 2020/07/31
    
## :exclamation: Если что-то не работает
То первым делом проверьте

    sestatus
    
Если он в enabled - отключите: откройте /etc/selinux/config и установите SELINUX в disabled

    

## С удовольствием приму все замечания

Если вам пригодилась эта штука - можно в качестве благодарности купить мне кофе! :) Но это совершенно не обязательно!

<a href="https://www.buymeacoffee.com/philyuchkoff" target="_blank"><img src="http://public.jc21.com/github/by-me-a-coffee.png" alt="Buy Me A Coffee" style="height: 51px !important;width: 217px !important;" ></a>
