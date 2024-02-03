import os
from datetime import datetime
import json
import pytz
import requests

def handler(pd: "pipedream"):

    HALO_SECRET = os.environ['HALO_SECRET']
    HALO_CLIENT_ID = os.environ['HALO_CLIENT_ID']
    HALO_AUTH_URL = os.environ['HALO_AUTH_URL']
    HALO_RESOURCE_URL = os.environ['HALO_RESOURCE_URL']
    HALO_TENANT = os.environ['HALO_TENANT']
    TEAM = 'NZ - Service Desk'

    CREATE_TICKET_URL = HALO_RESOURCE_URL + '/Tickets'
    CLIENTS_URL = HALO_RESOURCE_URL + '/Client'
    ACTIONS_URL = HALO_RESOURCE_URL + '/Actions'

    auth_body = { 
           'grant_type': 'client_credentials',
           'client_id': HALO_CLIENT_ID,
           'client_secret': HALO_SECRET,
           'scope': 'all'
    }

    access_token = requests.post(HALO_AUTH_URL, data=auth_body, timeout=10).json().get('access_token')


    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }


    def get_client_id(client_name):
        """Returns the client id for a given client name"""
        client = requests.get(CLIENTS_URL + f'?search={client_name}', headers=headers, timeout=10).json()
        return client.get('clients')[0].get('id')


    client_name = pd.steps["trigger"]["event"]["fields"]["halo_customer (from sitename)"][0]
    hostname = pd.steps["trigger"]["event"]["fields"]["hostname"]
    alert_type = pd.steps["trigger"]["event"]["fields"]["alert_type"]
    alert = pd.steps["trigger"]["event"]["fields"]["alert"]
    alert_message = pd.steps["trigger"]["event"]["fields"]["alert_message"]
    last_user = pd.steps["trigger"]["event"]["fields"]["last_user"]
    alert_category = pd.steps["trigger"]["event"]["fields"]["alert_category"]
    alert_time = datetime.now(pytz.timezone('Pacific/Auckland')).strftime('%d/%m/%Y %H:%M')

    if pd.steps["trigger"]["event"]["type"] == 'new_record':


        ticket_text = f"""<p><b>Monitor Alert Notice</b></p>
        <br>
        <p>An alert was triggered for a monitor configured for site {client_name} on {hostname}</p>
        <br>
        <p>The monitor is as follows:</p>
        <br>
        <p>{alert_category} monitor for {alert_type} to alert if {alert}</p>
        The alert was triggered at: {alert_time}</p>"""


        ticket_payload = {   
            "dateoccured": datetime.now().isoformat(),
            "summary": f'{hostname} | {client_name} | {alert_type} | {alert}', # Needs customizing
            "details_html": ticket_text,
            "client_id": get_client_id(client_name),
            "client_name": client_name,
            "team": TEAM,
            "impact": "2",
            "urgency": "2",
            "status_id": 1,
            "tickettype_id": "35"
        }

        json_payload = json.dumps([
            ticket_payload
            ])


        response = requests.post(CREATE_TICKET_URL, headers=headers, data=json_payload)

    elif pd.steps["trigger"]["event"]["type"] == 'record_modified':

        ticket_id = pd.steps["trigger"]["event"]["fields"]["HaloTicketID"]

        ticket_text = f"""<p><b>Monitor Alert Resolution Notice</b></p>
        <br>
        <p>An alert has been automatically resolved for a monitor configured for site {client_name} on {hostname}</p>
        <br>
        <p>The monitor is as follows:</p>
        <br>
        <p>{alert_category} monitor for {alert_type} to alert if {alert}</p>
        The alert was resolved at: {alert_time}</p>"""

        update_ticket_payload = {   
        "ticket_id": ticket_id,
        "note_html": ticket_text,
        "new_status": 9,
        "outcome_id": 4,  
        "sendemail": False,
        "customfields": [
            {
                "id": "215",
                "value": "8"
            }
        ]
        }

        json_payload = json.dumps([
        update_ticket_payload
        ])

        response = requests.post(ACTIONS_URL, headers=headers, data=json_payload)    

    return response.json()