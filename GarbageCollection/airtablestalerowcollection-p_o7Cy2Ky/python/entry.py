import requests
from datetime import datetime, timedelta
import os


def handler(pd: "pipedream"):
    
    # Array to store records that meet the criteria
    records_to_return = []

    # Current time
    current_time = datetime.now()

    # Address to send records to
    pipedream_function_url = os.environ["pipedream_delete_airtable_rows_url"]

    records = pd.steps["list_records"]["$return_value"]

    for record in records:
        status = record.get('fields').get('status')
        last_modified_string = record.get('fields').get('last_modified')

        # Convert last_modified to datetime object
        last_modified_date_time = datetime.strptime(last_modified_string, '%Y-%m-%dT%H:%M:%S.%fZ')

        # Check if the status is 'Closed' and last modified date is older than 24 hours
        if status == "Closed" and (current_time - last_modified_date_time > timedelta(hours=24)):
            # Make an HTTP request to another Pipedream function
            response = requests.post(pipedream_function_url, json=record)

                        # Assuming you want to collect records that successfully triggered the function
            if response.status_code == 200:
                records_to_return.append(record)


    return records_to_return
