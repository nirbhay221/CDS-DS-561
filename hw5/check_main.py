from wsgiref import headers
from flask import Flask, request, jsonify
from google.cloud import storage, logging, pubsub_v1
from google.oauth2 import service_account
import json
import os
from google.cloud.sql.connector import Connector, IPTypes
import pymysql

import socket, struct
import sqlalchemy
from sqlalchemy import text
import requests
from datetime import datetime
import sys
print(__name__)

app = Flask(__name__)


# Load service account key
service_account_key_file = "key.json"
credentials = service_account.Credentials.from_service_account_file(service_account_key_file)
PROJECT_ID = 'cdsds561-project-1'
DB_USER = 'root'
DB_PASS = 'admin'
DB_NAME = 'First-Trial'
INSTANCE_NAME= 'my-database'
REGION = 'us-east1'
INSTANCE_CONNECTION_NAME = f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"
# Initialize Google Cloud Storage, Logging, and Pub/Sub clients
storage_client = storage.Client.create_anonymous_client()
logging_client = logging.Client()
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)

print(f"Your instance connection name is: {INSTANCE_CONNECTION_NAME}")



connector = Connector()

# function to return the database connection object
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)


# with pool.connect() as db_conn:
#   # create ratings table in our sandwiches database
#   db_conn.execute(
#     sqlalchemy.text(
#       "CREATE TABLE IF NOT EXISTS ratings "
#       "( id SERIAL NOT NULL, name VARCHAR(255) NOT NULL, "
#       "origin VARCHAR(255) NOT NULL, rating FLOAT NOT NULL, "
#       "PRIMARY KEY (id));"
#     )
#   )

#   # commit transaction (SQLAlchemy v2.X.X is commit as you go)
#   db_conn.commit()

#   # insert data into our ratings table
#   insert_stmt = sqlalchemy.text(
#       "INSERT INTO ratings (name, origin, rating) VALUES (:name, :origin, :rating)",
#   )

#   # insert entries into table
#   db_conn.execute(insert_stmt, parameters={"name": "HOTDOG", "origin": "Germany", "rating": 7.5})
#   db_conn.execute(insert_stmt, parameters={"name": "BÀNH MÌ", "origin": "Vietnam", "rating": 9.1})
#   db_conn.execute(insert_stmt, parameters={"name": "CROQUE MADAME", "origin": "France", "rating": 8.3})

#   # commit transactions
#   db_conn.commit()

#   # query and fetch ratings table
#   results = db_conn.execute(sqlalchemy.text("SELECT * FROM ratings")).fetchall()

#   # show results
#   for row in results:
#     print(row)
with pool.connect() as conn:
    conn.execute(
        sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS Clients ("
            "client_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, "
            "gender VARCHAR(255) NOT NULL, "
            "age VARCHAR(255) NOT NULL, "
            "income VARCHAR(255) NOT NULL ); "
        )
    )
    conn.execute(
        sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS main_table ("
            "id INT AUTO_INCREMENT NOT NULL, "
            "client_id INT DEFAULT 1 NOT NULL,"
            "country VARCHAR(255) NOT NULL, "
            "client_ip VARCHAR(255) NOT NULL, "
            "is_banned BOOLEAN NOT NULL, "
            "time_of_day TIMESTAMP NOT NULL, "
            "requested_file VARCHAR(255) NOT NULL, "
            "PRIMARY KEY (id)," 
            "FOREIGN KEY (client_id) REFERENCES Clients(client_id) );"
        )
    )
    
    
    conn.execute(
        sqlalchemy.text(
        "CREATE TABLE IF NOT EXISTS error_log ("
        "id SERIAL PRIMARY KEY, "
        "time_of_request TIMESTAMP NOT NULL, "
        "requested_file VARCHAR(255) NOT NULL, "
        "error_code INT NOT NULL);"
        )
    )

    conn.commit()


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
        
        time_of_request = datetime.now()
        
        parts = path.split('/')
        last_part = parts[-1]
        requested_file = last_part

        with pool.connect() as conn:
            insert_error_stmt = sqlalchemy.text(
                "INSERT INTO error_log (time_of_request, requested_file, error_code) "
                "VALUES ( :time_of_request, :requested_file, :error_code)"
                        )
            
            conn.execute(
                insert_error_stmt,
                parameters={
                    "time_of_request": time_of_request,
                    "requested_file": requested_file,
                    "error_code":501,
                            }
                        )
            conn.commit()
        print(f"501 error") 
        return 'Method Not Implemented', 501

    elif method == "GET":
        components = path.split('/')
        bucket_name = components[0]
        directory_name = components[1]
        file_name = components[2]
        file_name = f"{directory_name}/{file_name}"

        # Extract the country information from the request headers, or use "Unknown" as a default
        country = request.headers.get("X-Country", "Unknown")
        client_ip = request.headers.get("X-Client-Ip", "Unknown")
        gender = request.headers.get("X-Gender", "Unknown")
        age = request.headers.get("X-Age", "Unknown")
        income = request.headers.get("X-Income", "Unknown")
        is_banned = True if country in banned_countries else False
        time_of_day = request.headers.get("X-Time", "Unknown")
        if time_of_day == "Unknown":
            time_of_day = datetime.now() 
        
        parts = path.split('/')
        last_part = parts[-1]
        requested_file = last_part
        print(f"Headers : {request.headers}")
        
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

#//////////////////////////////////////

                parts = path.split('/')
                last_part = parts[-1]
                requested_file = last_part
                time_of_request = datetime.now()
                with pool.connect() as conn:
                    insert_error_stmt = sqlalchemy.text(
                        "INSERT INTO error_log (time_of_request, requested_file, error_code) "
                        "VALUES ( :time_of_request, :requested_file, :error_code)"
                    )
                    conn.execute(
                        insert_error_stmt,
                        parameters={
                            "time_of_request":time_of_request,
                            "requested_file": requested_file,
                            "error_code": 403,
                            }
                        )
                    conn.commit()
                    print("ADDED TO ERROR_LOG")
                

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return 'Internal Server Error', 500

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
                if country not in banned_countries:
                    
                    parts = path.split('/')
                    last_part = parts[-1]
                    requested_file = last_part
                    client_id = 1
                    with pool.connect() as conn:
                        insert_clients_stmt = sqlalchemy.text(
                            "INSERT INTO Clients (gender, age, income) "
                            "VALUES (:gender, :age, :income)"
                            )
                        result = conn.execute(
                            insert_clients_stmt,
                            parameters={
                                "gender": gender,
                                "age": age,
                                "income": income,
                            }
                            )
                        conn.commit()
                        client_id = result.lastrowid
                        print(client_id)
                        
                        

                    with pool.connect() as conn:
                        insert_stmt = sqlalchemy.text(
                            "INSERT INTO main_table (client_id, country, client_ip, is_banned, time_of_day, requested_file) "
                            "VALUES ( :client_id, :country, :client_ip, :is_banned, :time_of_day, :requested_file)"
                            )
                        conn.execute(
                            insert_stmt,
                            parameters={
                            "client_id": client_id,
                            "country": country,
                            "client_ip": client_ip,
                            "is_banned": is_banned,
                            "time_of_day": time_of_day,
                            "requested_file": requested_file,
                            }
                        )
                
                        conn.commit()
                return contents, 200
            else:
                logging_client.logger("my-function-log").log_text(f"File Not Found. Error 404", severity="ERROR")

                
                parts = path.split('/')
                last_part = parts[-1]
                requested_file = last_part
                
                time_of_request = datetime.now()
                with pool.connect() as conn:
                    insert_error_stmt = sqlalchemy.text(
                        "INSERT INTO error_log (time_of_request, requested_file, error_code) "
                        "VALUES ( :time_of_request, :requested_file, :error_code)"
                    )
                    conn.execute(
                        insert_error_stmt,
                        parameters={
                            "time_of_request":time_of_request,
                            "requested_file": requested_file,
                            "error_code":404,
                            }
                        )
                    conn.commit()
                
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