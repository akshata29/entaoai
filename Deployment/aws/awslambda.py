import json
import uuid
import datetime
import requests
from requests.structures import CaseInsensitiveDict

def lambda_handler(event, context):
    print(json.dumps(event['Records'][0]['s3']['bucket']['name']))
    print(json.dumps(event['Records'][0]['s3']['object']['key']))
    s3bucketname = event['Records'][0]['s3']['bucket']['name']
    s3filename = event['Records'][0]['s3']['object']['key']
    random_uuid = uuid.uuid4()
    print(random_uuid)
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    print(date_string)
    
    url = "https://<yourtopic>.southcentralus-1.eventgrid.azure.net/api/events"
    headers = { "Content-Type": "application/json", "aeg-sas-key": "<yourkey>"}
    data = [ {"id": str(random_uuid), "eventType": "s3filereceived", "subject": "copyings3data", "eventTime": date_string, "data":{ "bucketname": s3bucketname, "filename": s3filename},"dataVersion": "1.0" , "metadataVersion": "1","topic": "/subscriptions/<yoursubscriptionid>/resourceGroups/<yourrg>/providers/Microsoft.EventGrid/topics/<youregtopic>"} ]
    
    print(headers)
    print(data)
    print(url)
    
    response = requests.post(url,headers=headers,data=json.dumps(data))
    print(response.status_code)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }