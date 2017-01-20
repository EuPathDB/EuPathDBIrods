# !/usr/bin/env python

import optparse
import json
import tempfile
import time
import os
import shutil
import tarfile
import requests
import sys
from requests.auth import HTTPBasicAuth
import contextlib

'''
 The following program is a Galaxy Tool for exporting gene list data from Galaxy to EuPathDB via IRODS.

 Sample for testing outside of Galaxy:
 python exportGeneListToEuPathDB.py "a name" "a summary" "a description" "PlasmoDB" "test-data/genelist.txt" "test-data/output.txt" "108976930"
'''

def __main__():

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()


    # Salt away all parameters.
    dataset_name = args[0]
    summary = args[1]
    description = args[2]
    project = args[3]
    dataset_file = args[4]
    results = args[5]
    user_id = args[6]
    # My WDK user id for now
    user_id = "108976930"

    # This msec timestamp is used to denote both the created and modified times.
    timestamp = int(time.time() * 1000)

    # TODO host, port, username and password will need to go into a configuration file somehow
    # TODO protocol should be SSL
    REST_URL = "http://wij.vm:8180/irods-rest/rest/fileContents/ebrc/workspaces/lz/"
    USER = "wrkspuser"
    PWD = "passWORD"

    # Names for the 2 json files and the folder containing the dataset to be included in the tarball
    META_JSON = "meta.json"
    DATASET_JSON = "dataset.json"
    DATAFILES = "datafiles"

    # Name given to this type of dataset and to the expected file
    GENE_LIST_TYPE = "GeneList"
    GENE_LIST_FILE = "genelist.txt"

    # This is the name of the file to be exported sans extension.  It will be used to designate a unique temporary
    # directory and to export both the tarball and the flag that triggers IRODS to process the tarball. By
    # convention, the dataset tarball is of the form dataset_uNNNNNN_tNNNNNNN.tgz where the NNNNNN following the _u
    # is the WDK user id and _t is the msec timestamp
    export_file_root = 'dataset_u' + user_id + '_t' + str(timestamp)

    # Create a unique temporary directory that serve as a staging area for assembling the tarball.
    orig_path = os.getcwd()
    with temporary_directory(export_file_root) as temp_path:
      os.mkdir(temp_path + "/" + DATAFILES)

      # Get the size of the gene list
      path, name = os.path.split(dataset_file)
      size = os.stat(dataset_file).st_size

      # Copy the gene list dataset file under the datafiles folder of the temporary dir and change the filename to genelist.txt since
      # the WDK expects that file name for this type of data.
      shutil.copy(dataset_file, temp_path + "/" + DATAFILES + "/" + GENE_LIST_FILE)

      # Create and populate the meta.json file that must be included in the tarball
      with open(temp_path + "/" + META_JSON, "w+") as metaFile:
        json.dump({"name": dataset_name,
              "description": description,
              "summary": summary}, metaFile, indent=4)

      # Create and populate the dataset.json file that must be included in the tarball
      # Don't know what the proper dependencies (if any) should be here
      with open(temp_path + "/" + DATASET_JSON, "w+") as datasetFile:
        json.dump({
          "type": {"name": GENE_LIST_TYPE, "version": "1.0"},
           "dependencies":
             [{"resourceIdentifier": "pf3d7_genome_rsrc",
               "resourceVersion": "12/2/2015",
               "resourceDisplayName": "pfal genome"},
              {"resourceIdentifier": "hsap_genome_rsrc",
               "resourceVersion": "2.6",
               "resourceDisplayName": "human genome"}
              ],
           "projects": [project],
           "owner": user_id,
           "size": size,
           "modified": timestamp,
           "created": timestamp
        }, datasetFile, indent=4)

      # The result file contains the information to be returned to the Galaxy user
      with open(results, "w+") as resultsFile:

        # Work inside the temporary directory.
        os.chdir(temp_path)

        # Package the tarball - contains meta.json, dataset.json and a datafiles folder containing the gene list file
        with tarfile.open(export_file_root + ".tgz", "w:gz") as tarball:
            for item in [META_JSON, DATASET_JSON, DATAFILES]:
                tarball.add(item)

        # Call the IRODS rest service to drop the tarball into the IRODS workspace landing zone
        dataset_response = send_request(REST_URL, export_file_root + ".tgz", USER, PWD)
        #resultsFile.write("Tarball - " + str(dataset_response.status_code) + "\n" + dataset_response.text + "\n")
        try:
          dataset_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
          print >> sys.stderr, "Error: " + str(e)
          sys.exit(os.EX_IOERR)

        # Create a empty (flag) file corresponding to the tarball
        open(export_file_root + ".txt", "w").close()

        # Call the IRODS rest service to drop a flag into the IRODS workspace landing zone.  This flag
        # triggers the IRODS PEP that unpacks the tarball and posts the event to Jenkins
        flag_response = send_request(REST_URL, export_file_root + ".txt", USER, PWD)
        #resultsFile.write("Flag - " + str(flag_response.status_code) + "\n" + flag_response.text + "\n")
        try:
          flag_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
          print >> sys.stderr, "Error: " + str(e)
          sys.exit(os.EX_IOERR)

        resultsFile.write("Your dataset has been successfully exported to EuPathDB\n")
        resultsFile.write("Please visit an appropriate EuPathDB site to view your dataset.")

      # Step out of the temp directory
      os.chdir(orig_path)


# This request is intended as a multi-part form post containing one file to be uploaded.  IRODS Rest does an iput
# followed by an iget, apparently.  So the response can be used to insure proper delivery.
def send_request(url, export_file, user, password):
  request = url + export_file
  headers = {"Accept": "application/json"}
  file = {"uploadFile": open(export_file, "rb")}
  auth = HTTPBasicAuth(user, password)
  try:
    response = requests.post(request, auth=auth, headers=headers, files=file)
  except requests.exceptions.ConnectionError as e:
    print >> sys.stderr, "Error: " + str(e)
    sys.exit(os.EX_IOERR)
  return response

# Creates a temporary directory such that removal is assured at end of program
@contextlib.contextmanager
def temporary_directory(dir_name):
  temp_path = tempfile.mkdtemp(dir_name)
  try:
    yield temp_path
  finally:
    shutil.rmtree(temp_path)

if __name__ == "__main__": __main__()