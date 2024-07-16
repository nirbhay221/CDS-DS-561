import argparse
import re
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions
from bs4 import BeautifulSoup
from google.cloud import storage
import logging  

from google.oauth2 import service_account
# Initialize global dictionaries to store outgoing and incoming links
outgoing_links = {}
incoming_links = {}

class ExtractLinksAndReadFileContent(beam.DoFn):
    def process(self, element):
        from bs4 import BeautifulSoup
        file_path = element

        # Google Cloud Storage client

#     # # Creating a storage Client using the provided service account's key
#         client = storage.Client.from_service_account_info(key_content)

        client = storage.Client()
        bucket_name = "hw2nirbhgsutil"
        directory_name = "test-dir"

        gcs_path = f"gs://{bucket_name}/{directory_name}/{file_path}"

        # Read the HTML content from the blob
        blob = client.get_bucket(bucket_name).get_blob(f"{directory_name}/{file_path}")
        content = blob.download_as_text()

        # Extract the file name from the GCS path
        file_name = file_path


        # Initialize outgoing_links for file_name as an empty set if it doesn't exist
        if file_name not in outgoing_links:
            outgoing_links[file_name] = set()  # Use a set to store unique outgoing links for each file

        soup = BeautifulSoup(content, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link.get('href')

            # regular expression to match the links correctly
            if re.match(r'\d+\.html', href):
                if href != file_name:
                    # Add the outgoing link 
                    outgoing_links[file_name].add(href)

        logging.info(f"Outgoing Dictionary Length:{len(outgoing_links)}")
        if len(outgoing_links) >= 10000:
            # Print the top 5 files with the most outgoing links
            print_top_files()
            # Calculate incoming links based on outgoing links
            calculate_incoming_links()
            # Print the top 5 files with the most incoming links
            print_top_incoming_files()

def print_top_files():
    global outgoing_links
    top_files = sorted(outgoing_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    for file_name, outgoing_count in top_files:
        logging.info(f'Top Outgoing Files: {file_name}, Outgoing Links Count: {len(outgoing_count)}')
        print(f'Top Outgoing Files: {file_name}, Outgoing Links Count: {len(outgoing_count)}')
    output_lines = [f'Top Outgoing Files: {file_name}, Outgoing Links Count: {len(outgoing_count)}' for file_name, outgoing_count in top_files]

    # Write the output to a file in the GCS bucket
    output_file_path = "gs://gcf-check-files/top_outgoing_files.txt"  
    _ = output_lines | 'WriteToFile' >> beam.io.WriteToText(output_file_path)


def calculate_incoming_links():
    global outgoing_links, incoming_links
    for file_name, outgoing_count in outgoing_links.items():
        for link in outgoing_count:
            if link not in incoming_links:
                incoming_links[link] = set()
            incoming_links[link].add(file_name)

def print_top_incoming_files():
    global incoming_links
    top_incoming_files = sorted(incoming_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    for file_name, incoming_count in top_incoming_files:
        logging.info(f'Top Incoming Files: {file_name}, Incoming Links Count: {len(incoming_count)}')
        print(f'Top Incoming Files: {file_name}, Incoming Links Count: {len(incoming_count)}')
    output_lines = [f'Top Incoming Files: {file_name}, Incoming Links Count: {len(incoming_count)}' for file_name, incoming_count in top_incoming_files]

    # Write the output to a file in the GCS bucket
    output_file_path = "gs://gcf-check-files/top_incoming_files.txt"  
    _ = output_lines | 'WriteToFile' >> beam.io.WriteToText(output_file_path)


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', required=True, help='GCS bucket containing HTML files')
    parser.add_argument('--directory', required=True, help='Directory within the GCS bucket')
    args, pipeline_args = parser.parse_known_args()

    # Update options to use the Dataflow runner
    options = PipelineOptions(pipeline_args)
    google_cloud_options = options.view_as(GoogleCloudOptions)
    options.view_as(beam.options.pipeline_options.StandardOptions).runner = "DataflowRunner"
    google_cloud_options.project = 'cdsds561-project-1'  
    google_cloud_options.temp_location = 'gs://gcf-check-files/temp'  # GCS location for temporary files
    google_cloud_options.region = 'us-east1'
    google_cloud_options.job_name = "hw7-nirb-gs"
    options.view_as(beam.options.pipeline_options.SetupOptions).save_main_session = True  # Enable saving main session
    with beam.Pipeline(options=options) as p:
        file_paths = [f'{i}.html' for i in range(10000)] 

        results = (
            p
            | 'ListFiles' >> beam.Create(file_paths)
            | 'ExtractLinksAndReadFileContent' >> beam.ParDo(ExtractLinksAndReadFileContent())
)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)  # Set the logging level to INFO
    run()
