from flask import Flask, request, jsonify
from google.cloud import storage, logging, pubsub_v1
from google.oauth2 import service_account
import json

import requests
print(__name__)

app = Flask(__name__)

# Load service account key
service_account_key_file = "key.json"
credentials = service_account.Credentials.from_service_account_file(service_account_key_file)

# Initialize Google Cloud Storage, Logging, and Pub/Sub clients
storage_client = storage.Client.create_anonymous_client()
logging_client = logging.Client()
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)

# Define the Pub/Sub topic for forbidden requests
topic_path = "projects/cdsds561-project-1/topics/hw3nirbhgsutil"

# List of banned countries
banned_countries = [
    "North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
    "Libya", "Sudan", "Zimbabwe", "Syria"
]

@app.route('/<path:path>', methods=['GET', 'PUT', 'POST', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def handle_request(path):
    method = request.method
    
    if method != "GET":
        # Handle unsupported HTTP methods
        logging_client.logger("my-function-log").log_text(f"Unsupported HTTP method: {method}", severity="ERROR")
       
        print(f"501 error") 
        return 'Method Not Implemented', 501

    elif method == "GET":
        components = path.split('/')
        bucket_name = components[0]
        directory_name = components[1]
        file_name = components[2]
        file_name = f"{directory_name}/{file_name}"

        # Extract the country information from the request headers, or use "Unknown" as a default
        country = request.headers.get("X-country", "Unknown")

        # Log the country information to Google Cloud Logging
        logging_client.logger("get-func-log").log_text(f"Country of origin: {country}")

        # Check if the request's country header is in the list of banned countries
        if country in banned_countries:
            try:
                # Send the entire request to the second app (pubsub)
                pubsub_message = {
                    "data": method,
                    "headers": dict(request.headers)
                }
                # Publisher publishes the message to the forbidden topic
                publish_to_pubsub(pubsub_message)
                print(f"Access from {country} is prohibited.")
            except Exception as e:
                return 'Error', 500

            return 'Access Denied', 403
        else:
            contents = get_file_contents(bucket_name, file_name)
            if contents is not None:
                logging_client.logger("my-function-log").log_text(f"File Found.")
                external_ip = get_external_ip()
                if external_ip:
                    print(f"External IP address: {external_ip}")
                else:
                    print("Unable to determine the external IP address")
                
                print(f"200 OK")
                return contents, 200
            else:
                logging_client.logger("my-function-log").log_text(f"File Not Found. Error 404", severity="ERROR")
                
                print(f"404 Error")
                return 'File Not Found', 404

def get_file_contents(bucket_name, file_name):
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        return blob.download_as_text()
    except Exception as e:
        logging_client.logger("get-func-log").log_text(f"Error while fetching file: {str(e)}")
        return None

def get_external_ip():
    try:
        response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip", headers={"Metadata-Flavor": "Google"})
        return response.text
    except Exception as e:
        print(f"Error fetching external IP: {str(e)}")
        return None
    
def publish_to_pubsub(message_data):
    # Encode the message data as JSON
    message_json = json.dumps(message_data)
    
    # Encode the JSON data as bytes
    data = message_json.encode("utf-8")
    print("Data", data)
    future = publisher_client.publish(topic_path, data=data)
    future.result()  # Ensure the message is published

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=80)
