echo "This script will:
1) install all modules need to run web2py on Ubuntu/Debian
2) install web2py in /home/www-data/
3) create a self signed sll certificate
4) setup web2py with mod_wsgi
5) overwrite /etc/apache2/sites-available/default
6) restart apache.

You may want to read this cript before running it.

Press a key to continue...[ctrl+C to abort]"

read CONFIRM

#!/bin/bash
# optional
# dpkg-reconfigure console-setup
# dpkg-reconfigure timezoneconf
# nano /etc/hostname
# nano /etc/network/interfaces
# nano /etc/resolv.conf
# reboot now
# ifconfig eth0

echo "installing useful packages"
echo "=========================="
apt-get update
yum install python2.5
yum install mod_wsgi
yum install emacs
httpd restart

echo "downloading, installing and starting web2py"
echo "==========================================="
cd /home
mkdir apache
cd apache
rm web2py_src.zip*
wget http://web2py.com/examples/static/web2py_src.zip
unzip web2py_src.zip
chown -R apache:apache web2py

mkdir /etc/httpd/ssl

echo "creating a self signed certificate"
echo "=================================="
openssl genrsa 1024 > /etc/httpd/ssl/self_signed.key
chmod 400 /etc/apache2/ssl/self_signed.key
openssl req -new -x509 -nodes -sha1 -days 365 -key /etc/httpd/ssl/self_signed.key > /etc/httpd/ssl/self_signed.cert
openssl x509 -noout -fingerprint -text < /etc/httpd/ssl/self_signed.cert > /etc/httpd/ssl/self_signed.info

echo "rewriting your apache config file to use mod_wsgi"
echo "================================================="
echo '
NameVirtualHost *:80
NameVirtualHost *:443

<VirtualHost *:80>
  WSGIDaemonProcess web2py user=apache group=apache
  WSGIProcessGroup web2py
  WSGIScriptAlias / /home/apache/web2py/wsgihandler.py

  <Directory /home/apache/web2py>
    AllowOverride None
    Order Allow,Deny
    Deny from all
    <Files wsgihandler.py>
      Allow from all
    </Files>
  </Directory>

  AliasMatch ^/([^/]+)/static/(.*) \
           /home/apache/web2py/applications/$1/static/$2
  <Directory /home/apache/web2py/applications/*/static/>
    Options -Indexes
    Order Allow,Deny
    Allow from all
  </Directory>

  <Location /admin>
  Deny from all
  </Location>

  <LocationMatch ^/([^/]+)/appadmin>
  Deny from all
  </LocationMatch>

  CustomLog /var/log/httpd/access.log common
  ErrorLog /var/log/httpd/error.log
</VirtualHost>

<VirtualHost *:443>
  SSLEngine on
  SSLCertificateFile /etc/httpd/ssl/self_signed.cert
  SSLCertificateKeyFile /etc/httpd/ssl/self_signed.key

  WSGIProcessGroup web2py

  WSGIScriptAlias / /home/apache/web2py/wsgihandler.py

  <Directory /home/apache/web2py>
    AllowOverride None
    Order Allow,Deny
    Deny from all
    <Files wsgihandler.py>
      Allow from all
    </Files>
  </Directory>

  AliasMatch ^/([^/]+)/static/(.*) \
        /home/apache/web2py/applications/$1/static/$2

  <Directory /home/apache/web2py/applications/*/static/>
    Options -Indexes
    ExpiresActive On
    ExpiresDefault "access plus 1 hour"
    Order Allow,Deny
    Allow from all
  </Directory>

  CustomLog /var/log/httpd/access.log common
  ErrorLog /var/log/httpd/error.log
</VirtualHost>
' > /etc/httpd/conf.d/sites/default

echo "restarting apage"
echo "================"

httpd -k restart
cd /home/apache/web2py
sudo -u apache python2.5 -c "from gluon.main import save_password; save_password(raw_input('admin password: '),443)"
echo "done!"
