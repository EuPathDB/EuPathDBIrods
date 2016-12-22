#!/usr/bin/env python

import requests
import sys
from urlparse import urlparse

# Utility method to take output of jobFile.txt (sent via IRODS), turn it into a series of http requests.
# Initial request is a get method to retrieve a crumb to be put in all subsequent request headers to avoid CSRF
# Each post request is called in turn.  An example parameter list is provided below
# (see sure to remove hashes and any spurious characters the editor may introduce)
# Done with the generous assistance of Mark Heiges

# Example parameter list
# "wrkspuser,be4797e4b88200492d29cf0aeb32f5de,http://wij.vm:9171/job/IrodsListener/build,eupathdbirods,otherstuff"


# This program resides in /var/lib/irods/iRODS/server/bin/cmd and is set as owned by irods.

def main():
  args = sys.argv[1:]
  if len(args) != 1:
    raise IOError("Expected a single string argument containing job file path, username, and password separated with commas.")
  props = "".join(args).split(",")
  username = props[0]
  password = props[1]
  jobUrl = props[2]
  token = props[3]
  datasetStoreId = props[4]
  host = urlparse(jobUrl).scheme + "://" + urlparse(jobUrl).hostname + ":" + str(urlparse(jobUrl).port)
  crumbUrl = host + "/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)"
  response = requests.get(crumbUrl, auth=(username, password))
  sys.stdout.write("Crumb retrieval Status Code: " + str(response.status_code) + "\n")
  crumbValue = response.text.split(":")[1]
  headers = {"Jenkins-Crumb":crumbValue}
  params = {"DATASET_STORE_ID": datasetStoreId, "token": token}
  response = requests.post(jobUrl, auth=(username, password), headers=headers, data=params)
  sys.stdout.write(" - Status Code: " + str(response.status_code) + "\n")
  sys.stdout.write("Complete\n")
  
if __name__ == "__main__":
    sys.exit(main())  