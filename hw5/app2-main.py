from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError
import json


from google.oauth2 import service_account
service_account_key_file ="key.json"

# Initialize a Pub/Sub subscriber client

# subscriber = pubsub_v1.SubscriberClient()
subscriber = pubsub_v1.SubscriberClient(credentials=service_account.Credentials.from_service_account_file(service_account_key_file))
project_id = "cdsds561-project-1" # project id
subscription_id = "hw3nirbhgsutil-sub" # subscription id created with the topic
# subscription_path = "projects/cdsds561-project-1/subscriptions/hw3nirbhgsutil-sub"  # subcscription path
subscription_path = subscriber.subscription_path(project_id,subscription_id) # subcscription path
def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        # Handle incoming Pub/Sub message
        pubsub_message = json.loads(message.data)
        headers = pubsub_message.get("headers", {})
        country = headers.get("X-Country", "Unknown") # Corrected header key

        # Process the message
        if country != 'Unknown':
            print(f"Received forbidden request from country: {country}")
            print("Error: Access is prohibited. Error 403")
        else:
            print("Received a forbidden request, but country information is missing in the headers.")

        # Acknowledge the message to remove it from the Pub/Sub topic
        message.ack()
    except Exception as e:
        print(f"Error: {str(e)}") 

# Subscribe to the Pub/Sub subscription and start listening for messages
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Keep the subscriber running and listening for messages indefinitely, it will end when CTRL+c is pressed
while True:
    pass