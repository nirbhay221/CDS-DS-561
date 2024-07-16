import argparse
import re
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from bs4 import BeautifulSoup
from apache_beam.io.gcp import gcsio

def extract_filename(file_path):
    return file_path.split('/')[-1]

# Initialize global dictionaries to store outgoing and incoming links
incoming_links = {}
outgoing_links = {}

def extract_links(element, file_path):
    content = element
    print(f'File Name: {file_path}')
    print(f'Content: {content[:100]}...')  # beginning of the content for demonstration purposes
    soup = BeautifulSoup(content, 'html.parser')
    file_name = file_path

    # Initialize outgoing_links for file_name as an empty set if it doesn't exist
    if file_name not in outgoing_links:
        outgoing_links[file_name] = set()  

    unique_incoming_links = set()

    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if re.match(r'\d+\.html', href):
            if href != file_name:
                # Add the outgoing link 
                outgoing_links[file_name].add(href)
                # Update the incoming links dictionary for the linked file
                if href not in incoming_links:
                    incoming_links[href] = set()  # Initialize the set for incoming links
                incoming_links[href].add(file_name)  # Add the linking filename



def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', required=True, help='GCS bucket containing HTML files')
    parser.add_argument('--directory', required=True, help='Directory within the GCS bucket')
    args, pipeline_args = parser.parse_known_args()

    options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=options) as p:
        results = (
            p
            | 'ListFiles' >> beam.Create([f'gs://{args.bucket}/{args.directory}/{i}.html' for i in range(10000)])
            | 'ExtractFilename' >> beam.Map(extract_filename)
            | 'ReadAndExtractLinks' >> beam.Map(lambda file_path: (file_path, gcsio.GcsIO().open(f'gs://{args.bucket}/{args.directory}/{file_path}').read()))
            | 'ProcessLinks' >> beam.Map(lambda element: extract_links(element[1], element[0]))
        )

    # Dictionary to store the count of incoming links for each file
    incoming_links_count = {}

    # Iterating the incoming links dictionary
    for file_name, links in incoming_links.items():
        incoming_links_count[file_name] = len(links)

    # Get the top 5 files with the most incoming links
    top_incoming_files = sorted(incoming_links_count.items(), key=lambda x: x[1], reverse=True)[:5]



    print("Top 5 files with the largest number of incoming links:")
    for file_name, incoming_count in top_incoming_files:
        print(f'File: {file_name}, Incoming Links Count: {incoming_count}')

    top_incoming_file_lines = [f'File: {file_name}, Incoming Links Count: {incoming_count}' for file_name, incoming_count in top_incoming_files]
    _ = top_incoming_file_lines | 'WriteTopIncomingFiles' >> beam.io.WriteToText(f'gs://gcf-check-files/test-dir/top_incoming_files.txt')


    # Get the top 5 files with the most outgoing links
    top_outgoing_files = sorted(outgoing_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]

    print("\nTop 5 files with the largest number of outgoing links:")
    for file_name, outgoing_count in top_outgoing_files:
        print(f'File: {file_name}, Outgoing Links Count: {len(outgoing_count)}')

    top_outgoing_file_lines = [f'File: {file_name}, Outgoing Links Count: {len(outgoing_count)}' for file_name, outgoing_count in top_outgoing_files]
    _ = top_outgoing_file_lines | 'WriteTopOutgoingFiles' >> beam.io.WriteToText(f'gs://gcf-check-files/test-dir/top_outgoing_files.txt')


if __name__ == '__main__':
    run()
