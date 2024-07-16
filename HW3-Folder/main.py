import requests
from google.cloud import pubsub_v1
import os
from flask import Flask, request
from google.cloud import storage
import json
from google.cloud import logging

from google.oauth2 import service_account

service_account_key_file = "key.json"

storage_client = storage.Client.create_anonymous_client()
logging_client = logging.Client()
# List of banned countries
banned_countries = [
    "North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
    "Libya", "Sudan", "Zimbabwe", "Syria"
]

# Publisher 
publisher_client = pubsub_v1.PublisherClient(credentials=service_account.Credentials.from_service_account_file(service_account_key_file))
# Topic to which publisher will publish
topic_path = "projects/cdsds561-project-1/topics/hw3nirbhgsutil"


def publish_to_pubsub(message_data):
    # Publish a message to the Pub/Sub topic
    data = message_data.encode("utf-8")  # Encode as bytes
    print("Data", data)
    future = publisher_client.publish(topic_path, data=data)
    future.result()  # Ensure the message is published


def get_file_contents(bucket_name, file_name):
    # Get file contents from the desired bucket
    try:
        bucket = storage_client.bucket(bucket_name) # bucket extracted
        blob = bucket.blob(file_name) # file extracted
        return blob.download_as_text() # file content extracted
    except Exception as e:
        logging_client.logger("get-func-log").log_text(f"Error while fetching file: {str(e)}")  
        return None

def get_file(request):
    if request.method == "GET": # GET Request Method
        path = request.path
        components = path.split('/')

        if len(components) != 4:
            return "Invalid URL path format.", 400
        bucket_name = components[1] # Extracting bucket name
        directory_name = components[2] # Extracting directory name
        file_name = components[3] # Extracting file name
        if not directory_name:
            return "Missing 'directory' parameter in the request.", 400  

        if not file_name:
            return "Missing 'name' parameter in the request.", 400

        full_file_name = f"{directory_name}/{file_name}"
        contents = get_file_contents(bucket_name, full_file_name)

        # Extract the country information from the request headers
        country = request.headers.get("X-country", "Unknown")

        # Log the country information to Google Cloud Logging
        logging_client.logger("get-func-log").log_text(f"Country of origin: {country}")

        # Check if the country is in the list of banned countries
        if country in banned_countries:
            # data_to_send = "Access from {country} is prohibited. Error 403"
            try:
            # Send the entire request to the second app
                pubsub_message = {
                    "data": request.data.decode('utf-8'),
                    "headers": dict(request.headers)
                    }
                # Publisher publishes the message to topic
                publish_to_pubsub(json.dumps(pubsub_message))
            except Exception as e:
                return f"Error: {str(e)}", 500

            return f"Access from {country} is prohibited.", 403  # Return a 403 Forbidden error
        elif contents is not None:
            logging_client.logger("my-function-log").log_text(f"File Found.")
            return contents, 200
        else:
            logging_client.logger("my-function-log").log_text(f"File Not Found. Error 404", severity="ERROR")
            return f"File '{full_file_name}' not found.", 404 

    else:
        # Handle other HTTP methods (PUT, POST, DELETE, HEAD, PATCH, TRACE , CONNECT, OPTIONS etc.)
        logging_client.logger("my-function-log").log_text(f"Unsupported HTTP method: {request.method}", severity="ERROR")
        return "Method not implemented.", 501 # Method Not Implemented Error
