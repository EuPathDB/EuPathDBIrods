#!/usr/bin/env python

import sys
import json
import time

# Utility to tack onto a string representation of the dataset.json file accompanying the user dataset, additional event information to be returned as json object that may be used as an event.
# Additionally an event file name is created and also returned using the event id timestamp.

# Below are 2 test argument lists.
# '{ "type": {"name": "RNA Seq", "version": "1.0"},"dependencies": [{"resourceIdentifier": "pf3d7_genome_rsrc",  "resourceVersion": "12/2/2015", "resourceDisplayName": "pfal genome"},  {"resourceIdentifier": "hsap_genome_rsrc",    "resourceVersion": "2.6",   "resourceDisplayName": "human genome"} ],"projects":["PlasmoDB","FungiDB"],"owner": 108976930,"size": 200000000,"created": 1231238088881}' 'install' '' ''
# '{ "type": {"name": "RNA Seq", "version": "1.0"},"dependencies": [{"resourceIdentifier": "pf3d7_genome_rsrc",  "resourceVersion": "12/2/2015", "resourceDisplayName": "pfal genome"},  {"resourceIdentifier": "hsap_genome_rsrc",    "resourceVersion": "2.6",   "resourceDisplayName": "human genome"} ],"projects":["PlasmoDB","FungiDB"],"owner": 108976930,"size": 200000000,"created": 1231238088881}' 'share' 'grant' '70521010'

# This program resides in /var/lib/irods/iRODS/server/bin/cmd and is set as owned by irods.


def main():

    args = sys.argv[1:]

    if len(args) != 5:
        raise IOError("Usage: python eventGenerator dataset_json_object event datasetId action recipient")
    # rawJson = ''.join(args).replace('\n','')  Newlines don't seem to be a problem in iRODS
    event_json = json.loads(args[0])
    event = args[1]
    dataset_id = args[2]
    action = args[3]
    recipient = args[4]
    event_json['eventId'] = int(time.time()*1000)
    event_json['event'] =  event
    event_json['datasetId'] = dataset_id
    if action != None and len(action) > 0 and recipient != None and len(recipient) > 0:
        event_json['action'] = action
        event_json['recipient'] = recipient

    output = "event=" + json.dumps(event_json) + "%event_file_name=" + "event_" + str(event_json['eventId']) + ".json"

    sys.stdout.write(output)

if __name__ == "__main__":
    sys.exit(main())