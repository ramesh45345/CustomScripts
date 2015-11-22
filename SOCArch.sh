#!/bin/bash

set -e

if [ "$(id -u)" != "0" ]; then
	echo "Not running with root. Please run the script with su privledges."
	exit 1;
fi


OCDATAPATH=""

pacman -Syu --needed --noconfirm owncloud php-xcache php-intl php-mcrypt php-apache mariadb ffmpeg openssl

if [ -d /usr/share/webapps/owncloud ]; then
	OCLOCATION="/usr/share/webapps/owncloud"
elif [ -d /var/www/owncloud ]; then
	OCLOCATION="/var/www/owncloud"
else
	echo "Owncloud folder not detected. Exiting."
	exit 1;
fi
OCLOCALCONFIG="/etc/webapps/owncloud/config/config.php"

OCDEFAULTDATADIRECTORY="/usr/share/webapps/owncloud/data"
read -p "Input a OC data location (Default is $OCDEFAULTDATADIRECTORY): " OCDATADIRECTORY
OCDATADIRECTORY=$(readlink -f "${OCDATADIRECTORY%/}")
if [[ -z "$OCDATADIRECTORY" ]]; then
	echo "No input found. Defaulting to $OCDEFAULTDATADIRECTORY."
	OCDATADIRECTORY="$OCDEFAULTDATADIRECTORY"
elif [ -d "$OCDATADIRECTORY" ]; then
	echo "Setting OC data folder to ${OCDATADIRECTORY}"
else
	echo "Invalid setting. Exiting."
	exit 1;
fi

HTTPSPORT=64030
read -p "Input a HTTPS port (Default is $HTTPSPORT): " NEWHTTPSPORT
NEWHTTPSPORT=${NEWHTTPSPORT//[^0-9_]/}
if [[ -z "$NEWHTTPSPORT" ]]; then
	echo "No input found. Defaulting to $HTTPSPORT."
else
	echo "Setting HTTPS port to $NEWHTTPSPORT"
	HTTPSPORT=$NEWHTTPSPORT
fi

read -p "Press any key to continue." 
echo ""

set -u

if [ -d "$OCDATADIRECTORY" ]; then
	touch "${OCDATADIRECTORY}/.ocdata"
	chown http:http -R "$OCDATADIRECTORY"
	chown http:http "$OCDATADIRECTORY/../"
	chmod 755 "$OCDATADIRECTORY"
fi

chown -R http:http /usr/share/webapps/owncloud/

if [ ! -f /etc/httpd/conf/extra/owncloud.conf ]; then
	cp /etc/webapps/owncloud/apache.example.conf /etc/httpd/conf/extra/owncloud.conf
fi

# Uncomment lines in php.ini
sed -i '/^;.*=gd.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=iconv.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=xmlrpc.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=zip.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=bz2.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=curl.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=intl.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=mcrypt.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=openssl.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=pdo_mysql.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=mysql.so/s/^;//' /etc/php/php.ini
sed -i '/^;.*=xcache.so/s/^;//' /etc/php/conf.d/xcache.ini

# httpd.conf changes
sed -i '/^#LoadModule ssl_module modules\/mod_ssl.so/s/^#//g' /etc/httpd/conf/httpd.conf
sed -i '/^#LoadModule socache_shmcb_module modules\/mod_socache_shmcb.so/s/^#//g' /etc/httpd/conf/httpd.conf
sed -i '/^#Include conf\/extra\/httpd-ssl.conf/s/^#//g' /etc/httpd/conf/httpd.conf

if ! grep -q "^Include conf/extra/owncloud.conf" "/etc/httpd/conf/httpd.conf"; then
	echo "Include conf/extra/owncloud.conf" >> /etc/httpd/conf/httpd.conf
fi
	
if ! grep -q "^Include conf/extra/php5_module.conf" "/etc/httpd/conf/httpd.conf"; then
	echo "Include conf/extra/php5_module.conf" >> /etc/httpd/conf/httpd.conf
fi

if grep -q "^LoadModule mpm_event_module modules/mod_mpm_event.so" /etc/httpd/conf/httpd.conf; then
	sed -i '/^LoadModule mpm_event_module modules\/mod_mpm_event.so/s/^/#/g' /etc/httpd/conf/httpd.conf
	sed -i '/^#LoadModule mpm_prefork_module modules\/mod_mpm_prefork.so/s/^#//g' /etc/httpd/conf/httpd.conf
fi

if grep -q "^LoadModule dav_module modules/mod_dav.so" /etc/httpd/conf/httpd.conf; then
	sed -i '/^LoadModule dav_module modules\/mod_dav.so/s/^/#/g' /etc/httpd/conf/httpd.conf
fi

if grep -q "^LoadModule dav_fs_module modules/mod_dav_fs.so" /etc/httpd/conf/httpd.conf; then
	sed -i '/^LoadModule dav_fs_module modules\/mod_dav_fs.so/s/^/#/g' /etc/httpd/conf/httpd.conf
fi

if ! grep -q "^LoadModule php5_module modules/libphp5.so" /etc/httpd/conf/httpd.conf; then
	sed -i "/LoadModule dir_module modules\/mod_dir.so/aLoadModule php5_module modules\/libphp5.so" /etc/httpd/conf/httpd.conf
fi

sed -i "s/^Listen .*/Listen 127.0.0.1:80/" /etc/httpd/conf/httpd.conf

#Https changes
sed -i "s/^Listen .*/Listen "$HTTPSPORT" https/" /etc/httpd/conf/extra/httpd-ssl.conf
sed -i "s@^DocumentRoot .*@DocumentRoot \"${OCLOCATION}\"@" /etc/httpd/conf/extra/httpd-ssl.conf
sed -i "s/^<VirtualHost _default_:.*>/<VirtualHost _default_:${HTTPSPORT}>/" /etc/httpd/conf/extra/httpd-ssl.conf

#chown -R http:http /usr/share/webapps/owncloud/

if [ ! -f /etc/httpd/conf/server.crt ]; then
	echo "Generating openssh keys."
	openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out /etc/httpd/conf/server.key
	chmod 600 /etc/httpd/conf/server.key
	openssl req -new -key /etc/httpd/conf/server.key -out /etc/httpd/conf/server.csr -subj '/C=US/ST=SomeState/CN=Test'
	openssl x509 -req -days 3652 -in /etc/httpd/conf/server.csr -signkey /etc/httpd/conf/server.key -out /etc/httpd/conf/server.crt
fi

set +eu
if [ ! -f /var/lib/mysql/mysql-bin.000001 ]; then
	systemctl stop mysqld
	mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
	systemctl restart mysqld
	mysql_secure_installation
fi
set -eu

systemctl enable mysqld
systemctl restart mysqld
systemctl enable httpd
systemctl restart httpd

sleep 1

if [ ! -f "$OCLOCALCONFIG" ] || ! grep -q "'datadirectory'" "$OCLOCALCONFIG"; then
	xdg-open http://127.0.0.1/
fi

sleep 3

if [ -f "$OCLOCALCONFIG" ] && ! grep -q "memcache.local" "$OCLOCALCONFIG"; then
	sed -i "/'installed'/a\ \ \'memcache\.local\' => \'\\\OC\\\Memcache\\\XCache\'," "$OCLOCALCONFIG"
fi

if [ -f "$OCLOCALCONFIG" ] && ! $(grep "'datadirectory'" "$OCLOCALCONFIG" | grep -q "$OCDATADIRECTORY" "$OCLOCALCONFIG"); then
	echo "Changing OC data folder to ${OCDATADIRECTORY} in $OCLOCALCONFIG."
	sed -i "s@\('datadirectory' => '\)\(.*\)\(',\)@\1${OCDATADIRECTORY}\3@" "$OCLOCALCONFIG"
fi

if ! $(grep "php_admin_value" /etc/httpd/conf/extra/owncloud.conf | grep -q "$OCDATADIRECTORY" /etc/httpd/conf/extra/owncloud.conf); then
	echo "Changing OC data folder in /etc/httpd/conf/extra/owncloud.conf."
	sed -i "s@\(php_admin_value\ open_basedir.*/etc/webapps/owncloud\)\(.*\"\)@\1:$OCDATADIRECTORY\"@" /etc/httpd/conf/extra/owncloud.conf
fi



systemctl restart httpd

echo "Script finished successfully."
