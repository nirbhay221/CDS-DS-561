#!/usr/bin/env python3
import argparse
from google.cloud import storage
from google.oauth2 import service_account
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from html.parser import HTMLParser
import numpy as np
import random
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx

DAMPING_FACTOR = 0.85
CONVERGENCE_THRESHOLD = 0.005

# Dictionary for storing the total sum of outgoing and incoming links for each of the respective files in the test-dir directory.
store_dictionary = {

}
# Dictionary for updating the pagerank of each of the files in the test-dir directory and storing the pagerank of each file in the following dictionary.
pagerank_dictionary = {

}
# Following Dictionary contains all the outgoing links of each of the files.
outgoing_links_dictionary = {

}
# Following Dictionary contains all the incoming links of each of the files.
incoming_links_dictionary = {

}

# LINK PARSER : Used for Extracting Incoming and Outgoing Links.

class LinkParser:
    # Link Parser object is initialized with an empty set for storing links found in the HTML files.
    def __init__(self):
        self.links = set()  # Store all links found in the HTML file

    def parse(self, html_content, base_url):
        # Following Method Parses HTML content and extracts the links that match a specific pattern.
        # It takes two parameters : 'html content' ( the HTML content to parse ) and the 'base_url' (the base URL for relative links).

        # Beautiful Soup object is created for parsing the HTML content.
        soup = BeautifulSoup(html_content, 'html.parser')

        # Iterating through all the <a> elements in the HTML Content that have an 'href' attribute
        for link in soup.find_all('a', href=True):
            # We get the 'href' attribute value from the <a> element
            href = link.get('href')
            # We check if the 'href' attribute matches a specific pattern like 0.html, 1.html .. etc using a regular expression
            if re.match(r'\d+\.html', href):
                # If the 'href' patter matches, we add it to the set of links stored in the 'self.links' attribute.
                self.links.add(href)



# Used for Extracting Incoming Links from the HTML content.

def extract_incoming_links(html_content, base_url):
    # Following function takes two parameters : 'html_content' (The HTML content to parse) and 'base_url' (Base URL for relative links)

    # Use Beautiful Soup for parsing the HTML Content.
    soup = BeautifulSoup(html_content, 'html.parser')
    # Empty incoming links dictionary for storing incoming links
    incoming_links = {}
    # We iterate through all <a> elements in the HTML content that have an 'href' attribute
    for link in soup.find_all('a', href=True):
        # Here we get the value of the 'href' attribute
        href = link.get('href')
        if href:
            # We create the full URL here by joining the 'base_url' and 'href'
            full_url = urljoin(base_url, href)

            # Get the target file name from the URL
            target_file = re.search(r'(\d+\.html)', full_url)
            if target_file:
                # Target File found in the URL is extracted here.
                target_file = target_file.group(1)
                # It is just a check condition for checking if the target file name is already in the incoming_link dictionary.
                if target_file not in incoming_links:
                    # If it is not present in the dictionary, we add it to the dictionary with a count of 1.
                    incoming_links[target_file] = 1
                else:
                    # If it's already in the dictionary, we increment the count.
                    incoming_links[target_file] += 1
    # Return the incoming_links dictionary.
    return incoming_links

# Used for extracting outgoing links from the HTML content.

def extract_outgoing_links(html_content, base_url):
    # It takes two parameters : 'html_content' ( The HTML Content to parse ) and 'base_url' ( BASE_URL for relative links ).

    # Beautiful soup object is created for parsing the HTML Content.
    soup = BeautifulSoup(html_content, 'html.parser')
    # Empty outgoing_links dictionary initialized.
    outgoing_links = {}

    # Iterating through all <a> elements in the HTML content that have an 'href' attribute.
    for link in soup.find_all('a', href=True):
        # Retrieving value of the 'href' attribute.
        href = link.get('href')
        if href:
            # Full URL is created by combining 'base_url' and 'href'
            full_url = urljoin(base_url, href)
            # Get the target file name from the URL
            target_file = re.search(r'(\d+\.html)', full_url)
            if target_file:
                # We extract the target file name, if it is found in the URL.
                target_file = target_file.group(1)
                # Check if the target file name is already in the dictionary.
                if target_file not in outgoing_links:
                    # If it is not in the dictionary, add it to the dictionary with a count of 1.
                    outgoing_links[target_file] = 1
                else:
                    # If it's already in the dictionary increment the count by 1.
                    outgoing_links[target_file] += 1

    # Return the dictionary.
    return outgoing_links

# mean of a list of values.
def calculate_mean(values):

    if not values:
        return None
    return sum(values) / len(values)

#  median of a list of values.
def calculate_median(values):
    if not values:
        return None
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 1:
        return sorted_values[n // 2]
    else:
        mid1 = sorted_values[(n - 1) // 2]
        mid2 = sorted_values[n // 2]
        return (mid1 + mid2) / 2

# maximum value in a list of values.
def calculate_maximum(values):

    if not values:
        return None
    max_value = values[0]
    for value in values:
        if value > max_value:
            max_value = value
    return max_value
# minimum value in a list of values.
def calculate_minimum(values):
    if not values:
        return None
    min_value = values[0]
    for value in values:
        if value < min_value:
            min_value = value
    return min_value

# quintiles (20th, 40th, 60th, and 80th percentiles) of a list of values.
def calculate_quintiles(values):
    if not values:
        return [None, None, None, None]

    sorted_values = sorted(values)
    n = len(sorted_values)

    # Calculate the indices corresponding to the desired percentiles
    index20 = int(0.20 * (n - 1))
    index40 = int(0.40 * (n - 1))
    index60 = int(0.60 * (n - 1))
    index80 = int(0.80 * (n - 1))

    quintile20 = sorted_values[index20]
    quintile40 = sorted_values[index40]
    quintile60 = sorted_values[index60]
    quintile80 = sorted_values[index80]

    return [quintile20, quintile40, quintile60, quintile80]



def calculate_statistics(link_counts):
    # Filter out None values from input list of link counts (invalid counts)
    counts_list = [count for count in link_counts if count is not None]
    # If there are no valid counts after filtering, it return a tuple of None values.
    if not counts_list:
        # Handle the case where there are no valid counts
        return None, None, None, None, [None, None, None, None]
    # print("Stats with numpy :")
    # Calculate statistics : Mean , Median, Maximum and Mininmum.
    average = np.mean(counts_list)
    median = np.median(counts_list)
    maximum = max(counts_list)
    minimum = min(counts_list)

    # Calculate quintiles (20th, 40th, 60th, and 80th percentiles)
    quintiles = np.percentile(counts_list, [20, 40, 60, 80])

    return average, median, maximum, minimum, quintiles


def calculate_statistics_without_numpy(link_counts):
    # Filter out None values from input list of link counts (invalid counts)
    counts_list = [count for count in link_counts if count is not None]
    # If there are no valid counts after filtering, it return a tuple of None values.
    if not counts_list:
        # Handle the case where there are no valid counts
        return None, None, None, None, [None, None, None, None]
    print("Stats with numpy :")
    # Calculate statistics : Mean , Median, Maximum and Mininmum.
    average = calculate_mean(counts_list)
    median = calculate_median(counts_list)
    maximum = calculate_maximum(counts_list)
    minimum = calculate_minimum(counts_list)

    # Calculate quintiles (20th, 40th, 60th, and 80th percentiles)
    quintiles = calculate_quintiles(counts_list)

    return average, median, maximum, minimum, quintiles

# Used for analyzing incoming links for HTML Files in a Google cloud storage bucket's directory.

def analyze_incoming_links(gcs_bucket,directory_name):
    all_incoming_links = {}  # A dictionary to store incoming links for all files in the directory

    for blob in gcs_bucket.list_blobs(prefix=f"{directory_name}/"):
        # Read the HTML content from the blob
        content = blob.download_as_text()
        base_url = f"https://storage.googleapis.com/{gcs_bucket.name}/{directory_name}/{blob.name}"

        # Extract incoming links from the HTML content
        incoming_links = extract_incoming_links(content, base_url)

        # Incoming links are merged into the all_incoming_links dictionary

        for file_name, count in incoming_links.items():
            # Used for storing the incoming count for the store_dictionary for each file.
            store_dictionary[file_name] = {
                'incoming_links_count': incoming_links.get(blob.name, 0),
                'outgoing_links_count': 0
            }
            # Used for esuring that the dictionary contains a count of incoming links for each file encountered during the loop.
            if file_name in all_incoming_links:
                all_incoming_links[file_name] += count
            else:
                all_incoming_links[file_name] = count

    return all_incoming_links

def analyze_outgoing_links(gcs_bucket,directory_name):
    link_relations = {}  # A dictionary for storing outgoing links for each file

    for blob in gcs_bucket.list_blobs(prefix=f"{directory_name}/"):
        # Read the HTML content from the blob
        content = blob.download_as_text()
        base_url = f"https://storage.googleapis.com/{gcs_bucket.name}/{directory_name}/{blob.name}"

        # Extract outgoing links from the HTML content
        outgoing_links = extract_outgoing_links(content, base_url)

        # Calculate the total number of outgoing links for the current file
        total_outgoing_links = sum(outgoing_links.values())

        # Add the outgoing and incoming links to the dictionary
        link_relations[blob.name] = {
            'outgoing_links': outgoing_links,
            'total_outgoing_links': total_outgoing_links
        }

        # Update the store_dictionary using the correct file name.
        file_name = blob.name.split("/")[-1]  # Extract the file name without the "test-dir" prefix
        store_dictionary[file_name]['outgoing_links_count'] = total_outgoing_links

        # Print outgoing links for the current file
        outgoing_links_dictionary[file_name] = outgoing_links
        # print(f"File: {file_name}")
        # print(f"Outgoing Links: {outgoing_links}")
        # print(f"Total Outgoing Links: {total_outgoing_links}")
        # print()

    return link_relations

# Used for calculating Page Rank :

def calculate_pagerank(store_dictionary, incoming_links_dictionary, outgoing_links_dictionary, pagerank_dictionary):
    num_files = len(store_dictionary)

    # Page rank value for each file is initialized to be 1.0.
    pagerank_values = {file_name: 1.0/num_files for file_name in store_dictionary.keys()}  # Initialize with 1.0 as the initial value
    # Initializing Iteration Counter.
    iteration = 0
    # Damping factor for the Pagerank calculation.
    damping_factor = 0.85
    # Convergence Threshold for determining when to stop iteration.
    convergence_threshold = 0.005


    while True:  # Infinite loop until convergence
        new_pagerank_values = {}
        sum_pageranks = sum(pagerank_values.values())  # Calculate the sum of pageranks across all files

        # Iterate over each file in the store_dictionary
        for file_name in store_dictionary:
            # Extracting incoming and outgoing links of the current file
            incoming_links = incoming_links_dictionary.get(file_name, {})
            outgoing_links = outgoing_links_dictionary.get(file_name, {})
            new_pagerank = 0.15  # Start with the 0.15 as the initial value

            # Pagerank updated based on incoming links
            if incoming_links:
                for incoming_file in incoming_links:
                    if incoming_file in pagerank_values and incoming_file in outgoing_links_dictionary:
                        new_pagerank += (damping_factor * pagerank_values[incoming_file]) / len(outgoing_links_dictionary[incoming_file])

            # Store the current file's updated pagerank value
            new_pagerank_values[file_name] = new_pagerank

        # Update pagerank value with the newly evaluated value
        pagerank_values = new_pagerank_values

        # Increment the iteration counter
        iteration += 1

        # Check if the sum of pageranks changes by more than 0.5% across iterations
        new_sum_pageranks = sum(pagerank_values.values())
        if abs(new_sum_pageranks - sum_pageranks) <= 0.005 * sum_pageranks:
            break

    # Final pagerank values are stored in the pagerank_dictionary
    for file_name, pagerank in pagerank_values.items():
        pagerank_dictionary[file_name] = pagerank

    # Print PageRank values after each iteration
    print(f"Iteration {iteration}:")
    # for file_name, pagerank in pagerank_values.items():
    #     print(f"File: {file_name}, PageRank: {pagerank:.6f}")

    print(f"Iteration {iteration} completed.")

    return pagerank_values


def print_incoming_links(all_incoming_links):
    # Used for updating the store_dictionary with the incoming links counts.
    for file_name, incoming_count in all_incoming_links.items():
        store_dictionary[file_name]['incoming_links_count'] = incoming_count

        # print(f"File: {file_name}")
        # print(f"Incoming Links Count: {incoming_count}")
        # print()


def print_graph(graph, graph_type):
    print(f"{graph_type} Links Graph:")
    for node, neighbors in graph.items():
        neighbor_nodes = ", ".join(neighbors)
        print(f"Node {node} -> {neighbor_nodes}")

def main():
    # Parse Command Line arguments for extracting bucket name

    parser = argparse.ArgumentParser()
    parser.add_argument('bucket_name', help="Specify the GCS bucket name to analyze")

    parser.add_argument('directory_name', help="Specify the GCS directory name to analyze")
    args = parser.parse_args()

    # Service Account's Key
    # credentials = service_account.Credentials.from_service_account_file("C:/Users/nirbh/Downloads/cdsds561-project-1-3185d9128a0f.json")
    # # Creating a storage Client using the provided service account's key
    # storage_client = storage.Client(project="cdsds561-project-1", credentials=credentials)
    storage_client = storage.Client.create_anonymous_client()
    gcs_bucket = storage_client.bucket(args.bucket_name)

    print(f"Analyzing incoming links within HTML files in bucket: {args.bucket_name}")

    # Analyze links and collect incoming links for all files
    all_incoming_links = analyze_incoming_links(gcs_bucket,args.directory_name)

    # Print the big dictionary of incoming links
    print_incoming_links(all_incoming_links)

    print(f"Analyzing outgoing links within HTML files in bucket: {args.bucket_name}")

    # Analyze links and collect outgoing links for all files
    analyze_outgoing_links(gcs_bucket,args.directory_name)

    # Randomly select a file from the store dictionary.
    # random_file_name = random.choice(list(store_dictionary.keys()))

    # # Check if the random file name exists in the store_dictionary
    # if random_file_name in store_dictionary:
    #     file_info = store_dictionary[random_file_name]
    #     incoming_links_count = file_info.get('incoming_links_count', 0)
    #     outgoing_links_count = file_info.get('outgoing_links_count', 0)

    #     # print(f"Random File Name: {random_file_name}")
    #     # print(f"Incoming Links Count: {incoming_links_count}")
    #     # print(f"Outgoing Links Count: {outgoing_links_count}")
    # else:
    #     print(f"File '{random_file_name}' not found in store_dictionary.")

    # Statistics Calculated for incoming links
    incoming_counts = [v.get('incoming_links_count') for v in store_dictionary.values()]
    incoming_average, incoming_median, incoming_max, incoming_min, incoming_quintiles = calculate_statistics(incoming_counts)

    # Calculate statistics for outgoing links
    outgoing_counts = [v.get('outgoing_links_count') for v in store_dictionary.values()]
    outgoing_average, outgoing_median, outgoing_max, outgoing_min, outgoing_quintiles = calculate_statistics(outgoing_counts)

    # Print the calculated statistics for both incoming and outgoing links.
    print("Statistics for Incoming Links:")
    print(f"Average: {incoming_average if incoming_average is not None else 'N/A'}")
    print(f"Median: {incoming_median if incoming_median is not None else 'N/A'}")
    print(f"Maximum: {incoming_max if incoming_max is not None else 'N/A'}")
    print(f"Minimum: {incoming_min if incoming_min is not None else 'N/A'}")
    print(f"Quintiles: {incoming_quintiles if incoming_quintiles[0] is not None else 'N/A'}")

    print("\nStatistics for Outgoing Links:")
    print(f"Average: {outgoing_average if outgoing_average is not None else 'N/A'}")
    print(f"Median: {outgoing_median if outgoing_median is not None else 'N/A'}")
    print(f"Maximum: {outgoing_max if outgoing_max is not None else 'N/A'}")
    print(f"Minimum: {outgoing_min if outgoing_min is not None else 'N/A'}")
    print(f"Quintiles: {outgoing_quintiles if outgoing_quintiles[0] is not None else 'N/A'}")



    incoming_counts = [v.get('incoming_links_count') for v in store_dictionary.values()]
    incoming_average, incoming_median, incoming_max, incoming_min, incoming_quintiles = calculate_statistics_without_numpy(incoming_counts)

    # Calculate statistics for outgoing links
    outgoing_counts = [v.get('outgoing_links_count') for v in store_dictionary.values()]
    outgoing_average, outgoing_median, outgoing_max, outgoing_min, outgoing_quintiles = calculate_statistics_without_numpy(outgoing_counts)

    # Print the calculated statistics for both incoming and outgoing links.
    print("Statistics for Incoming Links without Numpy:")
    print(f"Average: {incoming_average if incoming_average is not None else 'N/A'}")
    print(f"Median: {incoming_median if incoming_median is not None else 'N/A'}")
    print(f"Maximum: {incoming_max if incoming_max is not None else 'N/A'}")
    print(f"Minimum: {incoming_min if incoming_min is not None else 'N/A'}")
    print(f"Quintiles: {incoming_quintiles if incoming_quintiles[0] is not None else 'N/A'}")

    print("\nStatistics for Outgoing Links without Numpy:")
    print(f"Average: {outgoing_average if outgoing_average is not None else 'N/A'}")
    print(f"Median: {outgoing_median if outgoing_median is not None else 'N/A'}")
    print(f"Maximum: {outgoing_max if outgoing_max is not None else 'N/A'}")
    print(f"Minimum: {outgoing_min if outgoing_min is not None else 'N/A'}")
    print(f"Quintiles: {outgoing_quintiles if outgoing_quintiles[0] is not None else 'N/A'}")



    num_files_in_store = len(store_dictionary)
    num_files_in_store = len(store_dictionary)
    print(f"Number of files in store_dictionary: {num_files_in_store}")

    # # Check the length of pagerank_dictionary
    # num_files_processed = len(pagerank_dictionary)
    # print(f"Number of files processed for PageRank: {num_files_processed}")

    files = list(store_dictionary.keys())
    incoming_links = [store_dictionary[file].get('incoming_links_count', 0) for file in files]
    outgoing_links = [store_dictionary[file].get('outgoing_links_count', 0) for file in files]

    # Create a new figure
    # Create a new figure with a wider width and increased height
    # Create a new figure
    # Create a new figure with a wider width
    # Create a new figure with a wider width

    # New figure
    # plt.figure(figsize=(12, 8))

    # # Scatter plot to represent incoming links
    # plt.scatter(range(len(files)), incoming_links, label='Incoming Links', color='blue', marker='o')

    # # Scatter plot to represent outgoing links
    # plt.scatter(range(len(files)), outgoing_links, label='Outgoing Links', color='green', marker='s')

    # # Labels for the x-axis
    # plt.xticks(range(len(files)), files, fontsize=8, rotation=90)

    # # Labels for the y-axis
    # plt.ylabel('Number of Links', fontsize=12)

    # # The title of the graph
    # plt.title('Incoming and Outgoing Links for Files', fontsize=14)

    # plt.legend()

    # plt.grid()
    # plt.show()


    # Dataframe for storing incoming and outgoing links for each file
    link_matrix = pd.DataFrame(columns=['File', 'Incoming Links', 'Outgoing Links'])
    # Incoming and Outgoing links are extracted from the store_dictionary.
    for file_name, file_info in store_dictionary.items():
        incoming_links_count = file_info.get('incoming_links_count', 0)
        outgoing_links_count = file_info.get('outgoing_links_count', 0)

        # Add a row to the link matrix DataFrame
        link_matrix = pd.concat([link_matrix, pd.DataFrame({'File': [file_name], 'Incoming Links': [incoming_links_count], 'Outgoing Links': [outgoing_links_count]})], ignore_index=True)

    # Link matrix printed.
    print("Link Matrix:")
    print(link_matrix)

    # Link matrix written to a CSV file
    link_matrix.to_csv('link_matrix.csv', index=False)

    # Empty incoming links dictionary for each file is initialized
    for file_name in outgoing_links_dictionary.keys():
        incoming_links_dictionary[file_name] = {}

    # Outgoing links dictionary is iterated for providing incoming links
    for source_file, outgoing_links in outgoing_links_dictionary.items():
        for target_file in outgoing_links:
            #  target file is checked if it is a valid file in the incoming links dictionary
            if target_file not in incoming_links_dictionary:
                incoming_links_dictionary[target_file] = {}

            # Source file is added to the incoming links of the target file, excluding self-links
            if source_file != target_file:
                incoming_links_dictionary[target_file][source_file] = 1

    # Incoming_links_dictionary printed.
    # for file_name, incoming_links in incoming_links_dictionary.items():
    # print(f"File: {file_name}")
    # print(f"Incoming Links: {list(incoming_links.keys())}")
    # print()

    file_ratios = []

    # Calculate the ratio for each file
    for file_name, file_info in store_dictionary.items():
        incoming_links_count = file_info.get('incoming_links_count', 0)
        outgoing_links_count = file_info.get('outgoing_links_count', 0)

        # Avoid division by zero
        if outgoing_links_count > 0:
            ratio = incoming_links_count / outgoing_links_count
        else:
            ratio = 0.0

        file_ratios.append((file_name, ratio))

    # Sort the list of tuples based on the ratio in descending order
    sorted_file_ratios = sorted(file_ratios, key=lambda x: x[1], reverse=True)

    # Print the top 5 files with the largest ratio
    # print("\nTop 5 Files with the Largest Ratio of Incoming Links to Outgoing Links:")
    # for i, (file_name, ratio) in enumerate(sorted_file_ratios[:5], 1):
    #     print(f"{i}. File: {file_name}, Ratio: {ratio:.6f}")


    print('Analyzing Page Rank .... ')

    pagerank_dictionary = {}  # Create an empty dictionary for storing PageRank values

    pagerank_values = calculate_pagerank(store_dictionary, incoming_links_dictionary, outgoing_links_dictionary, pagerank_dictionary)

    # Print PageRank for each file
    # for file_name, pagerank in pagerank_dictionary.items():
    #     print(f"File: {file_name}, PageRank: {pagerank:.6f}")

    # Sort the pagerank_values by PageRank in descending order
    sorted_pagerank = sorted(pagerank_values.items(), key=lambda x: x[1], reverse=True)

    print("\nTop 5 Pages by PageRank:")
    for i, (file_name, pagerank) in enumerate(sorted_pagerank[:5], 1):
        print(f"{i}. Page: {file_name}, PageRank: {pagerank:.6f}")


    # Empty outgoing links matrix created
    outgoing_links_matrix = pd.DataFrame(0, columns=files, index=files)

    # outgoing links dictionary iterated
    for source_file, outgoing_links in outgoing_links_dictionary.items():
        for target_file in outgoing_links:
            # Removing self-loops
            if source_file != target_file:
                # Set the corresponding cell to 1 to indicate an outgoing link
                outgoing_links_matrix.at[source_file, target_file] = 1

    # Print the outgoing links matrix
    print("Outgoing Links Matrix:")
    print(outgoing_links_matrix)

    # Save the outgoing links matrix to a CSV file
    outgoing_links_matrix.to_csv('outgoing_links_matrix.csv')



    # Outgoing links matrix saved to a CSV file
    outgoing_links_matrix.to_csv('outgoing_links_matrix.csv')
    # Empty incoming links matrix created.
    incoming_links_matrix = pd.DataFrame(0, columns=files, index=files)

    # Iterate through the incoming links dictionary
    for target_file, incoming_links in incoming_links_dictionary.items():
        for source_file in incoming_links:
            # Exclude self-loops
            if source_file != target_file:
                # Set the corresponding cell to 1 to indicate an incoming link
                incoming_links_matrix.at[target_file, source_file] = 1

    # Print the incoming links matrix
    print("Incoming Links Matrix:")
    print(incoming_links_matrix)

    # Save the incoming links matrix to a CSV file
    incoming_links_matrix.to_csv('incoming_links_matrix.csv')



    # Create dictionaries for incoming and outgoing links
    outgoing_links_graph = outgoing_links_dictionary
    incoming_links_graph = incoming_links_dictionary

    # # Print the outgoing links graph
    # print_graph(outgoing_links_graph, "Outgoing")

    # # Print the incoming links graph
    # print_graph(incoming_links_graph, "Incoming")







if __name__ == "__main__":
    main()







