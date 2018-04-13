#!/usr/bin/env python

import sys
import json
import time
import os

"""
Utility to tack onto a string representation of the dataset.json file accompanying the user dataset, additional event information
to be returned as json object that may be used as an event.  Additionally an event file name is created and also returned using
the event id timestamp.  The argument list contains:

1.  The dataset.json content of the subject dataset
2.  The event (i.e., 'install', 'uninstall', 'share')
3.  The id of the subject dataset
4.  The event action (applies only to share events and may be 'grant' or 'revoke')
5.  The id of the receiving user (applies only to share events)

Below is a sample test argument list for an install.
'{
    "created": 1491411125511,
    "dependencies": [
        {
            "resourceDisplayName": "pfal genome",
            "resourceVersion": "12/2/2015",
            "resourceIdentifier": "pf3d7_genome_rsrc"
        },
        {
            "resourceDisplayName": "human genome",
            "resourceVersion": "2.6",
            "resourceIdentifier": "hsap_genome_rsrc"
        }
    ],
    "owner": "108976930",
    "type": {
        "version": "1.0",
        "name": "GeneList"
    },
    "projects": [
        "plasmoDB"
    ],
    "size": 42
}'   'install'  '15181'  ''  ''


This program resides in /var/lib/irods/iRODS/server/bin/cmd and is set as owned by irods.  Be sure that perms are
755 (even if symlinked).
"""

def main():

    args = sys.argv[1:]

    try:
      if len(args) != 5:
          raise IOError("Usage: python eventGenerator dataset_json_object event datasetId action recipient")
      # rawJson = ''.join(args).replace('\n','')  Newlines don't seem to be a problem in iRODS
      event_json = json.loads(args[0])
      event = args[1]
      dataset_id = args[2]
      action = args[3]
      recipient = args[4]
      pid = '{0:0>8}'.format(str(os.getpid()))
      uuid = str(int(time.time())) + pid
      event_json['eventId'] = int(uuid)
      event_json['event'] =  event
      event_json['datasetId'] = dataset_id
      if action != None and len(action) > 0 and recipient != None and len(recipient) > 0:
          event_json['action'] = action
          event_json['recipient'] = recipient

      output = "event=" + json.dumps(event_json) + "%event_file_name=" + "event_" + str(event_json['eventId']) + ".json"
      sys.stdout.write(output)

    # Intended to provide diagnostic information back to the IRODS server log.  Otherwise the msiExecCmd can fail
    # without explanation.
    except Exception as e:
      sys.stdout.write(str(e))
      sys.exit(1)



if __name__ == "__main__":
    sys.exit(main())