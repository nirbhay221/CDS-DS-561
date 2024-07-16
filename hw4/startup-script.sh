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


GCS_BUCKET="hw4nirbhgsutil"
OBJECT_NAME="key.json"
gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME .
GCS_BUCKET="hw4nirbhgsutil"
OBJECT_NAME="main.py"
echo "Copying $OBJECT_NAME from Google Cloud Storage..."
gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME .
echo "Executing main.py..."

python3 main.py