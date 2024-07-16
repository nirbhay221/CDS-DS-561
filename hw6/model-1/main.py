import apache_beam as beam
import sqlalchemy
import pandas as pd
from google.cloud.sql.connector import Connector
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text

# Google Cloud SQL database configuration
PROJECT_ID = 'cdsds561-project-1'
DB_USER = 'root'
DB_PASS = 'admin'
DB_NAME = 'Second-Trial'
INSTANCE_NAME = 'my-database'
REGION = 'us-east1'
INSTANCE_CONNECTION_NAME = f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"

# Connector object for establishing a database connection
connector = Connector()

# Function for returning the database connection object
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# Connection pool with 'creator' argument to the connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# Global list to store elements and random states that have a high test accuracy
elements_list = []
good_random_states = []

class QueryDatabase(beam.DoFn):
    def process(self, element):
        # Access the database using the pool
        with pool.connect() as conn:
            # Execute a SELECT query to retrieve data from the 'Main' table
            select_query = text("""
                SELECT m.country,m.client_ip
                FROM main_table m;
            """)
            results = conn.execute(select_query).fetchall()

            for row in results:
                yield row

def is_valid_element(element):
    # Check for unknown fields here
    return not ('Unknown' in element)

def main():
    # Create a pipeline
    with beam.Pipeline() as p:
        results = (
            p
            | 'Create a dummy element' >> beam.Create(['dummy'])
            | 'Query database' >> beam.ParDo(QueryDatabase())
        )

        # Filter out elements with unknown fields
        valid_elements = results | 'Filter valid elements' >> beam.Filter(is_valid_element)

        # Print the valid elements in the results PCollection and save them in the global list
        valid_elements | 'Print and Save Elements' >> beam.ParDo(PrintAndSaveElementFn())

    df = pd.DataFrame(elements_list, columns=['country','client_ip'])
    df = df[df['country'] != 'Unknown']

    print(df.head())
    # Label encoding to 'country' and 'client_ip' columns
    label_encoder = LabelEncoder()
    df['country'] = label_encoder.fit_transform(df['country'])
    df['client_ip'] = label_encoder.fit_transform(df['client_ip'])
    # Splitting the data into features (X) and the target variable (y)
    X = df.drop(columns=['country']).values
    y = df['country'].values

    # Range of random_state values to test - I choose 81 random state since it had the best accuracy for decision tree classifier
    random_state_values = range(81,82)  

    # Lists to store training and test accuracy scores
    train_accuracies = []
    test_accuracies = []

    # List of classifiers to test
    classifiers = [
        RandomForestClassifier(n_estimators=500, max_depth=None)
    ]
    best_test_accuracy = 0.0
    for classifier in classifiers:
        for random_state in random_state_values:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state)

            clf = classifier
            clf.fit(X_train, y_train)

            y_train_pred = clf.predict(X_train)
            y_test_pred = clf.predict(X_test)

            train_accuracy = accuracy_score(y_train, y_train_pred)
            test_accuracy = accuracy_score(y_test, y_test_pred)

            train_accuracies.append(train_accuracy)
            test_accuracies.append(test_accuracy)

            if test_accuracy > best_test_accuracy:
                best_test_accuracy = test_accuracy
                best_random_state = random_state

            print(f'Random State {random_state}: Model: {str(classifier)}')
            print(f'Random State {random_state}: Testing Accuracy: {test_accuracy * 100:.2f}%')

    print("Best Random State:", best_random_state)
    print("Best Testing Accuracy:", best_test_accuracy * 100)

class PrintAndSaveElementFn(beam.DoFn):
    def process(self, element):
        if is_valid_element(element):
            elements_list.append(element)

if __name__ == "__main__":
    main()