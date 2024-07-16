#!/bin/bash
mkdir -p ./tmp
cd ./tmp/
echo "Updating package list..."
sudo apt update -y
echo "Installing Python 3..."
sudo apt install -y python3
echo "Installing Python 3 pip..."
sudo apt install -y python3-distutils python3-lib2to3
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
echo "Installing Google Cloud Python libraries..."
python3 -m pip install google-cloud-storage
python3 -m pip install google-cloud-logging
python3 -m pip install google-cloud-pubsub
python3 -m pip install google-auth
python3 -m pip install google-auth-oauthlib
python3 -m pip install google-cloud-storage

python3 -m pip install flask
echo "Installing Google Cloud SDK..."
sudo apt-get install -y google-cloud-sdk


echo "Installing Google Cloud SQL..."

sleep 30
/usr/bin/wget https://dev.mysql.com/get/Downloads/MySQL-8.2/mysql-server_8.2.0-1debian11_amd64.deb-bundle.tar
/bin/tar -xvf /path/to/mysql-server_8.2.0-1debian11_amd64.deb-bundle.tar

sudo apt-get install libaio1


echo "Check - 1 "

sudo dpkg-preconfigure mysql-community-server_*.deb

echo "Check - 2 "

sudo dpkg -i mysql*.deb

echo "Check - 3 "

sudo apt-get -f install


echo "Check - 4 "
python3 -m pip install pymysql

python3 -m pip install sqlalchemy

python3 -m pip install "cloud-sql-python-connector[pymysql]"

GCS_BUCKET="hw4nirbhgsutil"
OBJECT_NAME="key.json"
gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME .
GCS_BUCKET="hw4nirbhgsutil"
OBJECT_NAME="check_main.py"
echo "Copying $OBJECT_NAME from Google Cloud Storage..."
gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME .
echo "Executing check_main.py..."

python3 check_main.py
