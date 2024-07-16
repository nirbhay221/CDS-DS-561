FROM python:3.8-slim-buster

WORKDIR /app

COPY . /app

RUN apt-get update -y && \
    apt-get install -y python3-distutils python3-lib2to3 && \
    apt-get install -y python3-pip && \
    pip install --upgrade pip && \
    pip install google-cloud-storage google-cloud-logging google-cloud-pubsub google-auth google-auth-oauthlib flask

# wget, gnupg, and dirmngr installation
RUN apt-get install -y wget gnupg dirmngr

# Google Cloud SDK installation
RUN wget -qO- https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz | tar -xz -C /usr/local
RUN /usr/local/google-cloud-sdk/install.sh

ENV PATH $PATH:/usr/local/google-cloud-sdk/bin

ENV GCS_BUCKET="hw4nirbhgsutil"
ENV OBJECT_NAME_KEY="key-2.json"
ENV OBJECT_NAME_MAIN="main-2.py"

# Copying files
RUN gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME_KEY . && \
    gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME_MAIN .

# gcloud installation verification by listing files in the current directory
RUN gcloud auth activate-service-account --key-file=$OBJECT_NAME_KEY
EXPOSE 80

CMD ["python3", "main-2.py"]