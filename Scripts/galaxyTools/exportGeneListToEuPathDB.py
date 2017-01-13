# !/usr/bin/env python

import optparse
from json import dump
import tempfile
import time
import os
import shutil
import tarfile
import requests
from requests.auth import HTTPBasicAuth

'''
 The following program is a Galaxy Tool for exporting gene list data from Galaxy to EuPathDB via IRODS.

 Sample for testing outside of Galaxy:
 python exportGeneListToEuPathDB.py "a name" "a description" "a summary" "test-data/genelist.txt" "test-data/output.txt" "108976930"
'''

def __main__():

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    timestamp = int(time.time() * 1000)

    datasetName = args[0]
    description = args[1]
    summary = args[2]
    datasetFile = args[3]
    results = args[4]
    userId = args[5]
    # My WDK user id for now
    userId = "108976930"

    # Create a unique temporary directory that serve as a staging area for assembling the tarball.
    tempPath = tempfile.mkdtemp('dataset_u' + userId + '_t' + str(timestamp))
    os.mkdir(tempPath + "/datafiles")

    path, name = os.path.split(datasetFile)
    size = os.stat(datasetFile).st_size

    # Copy the gene list dataset file under the datafiles folder of the temporary dir and change the filename to genelist.txt
    shutil.copy(datasetFile, tempPath + "/datafiles/genelist.txt")
    with open(tempPath + "/meta.json", "w+") as metaFile:
        dump({'name': datasetName,
              'description': description,
              'summary': summary}, metaFile, indent=4)

    # Create and populate the dataset.json file that must be included in the tarball
    with open(tempPath + "/dataset.json", "w+") as datasetFile:
        dump({
          "type": {"name": "GeneList", "version": "1.0"},
           "dependencies":
             [{"resourceIdentifier": "pf3d7_genome_rsrc",
               "resourceVersion": "12/2/2015",
               "resourceDisplayName": "pfal genome"},
              {"resourceIdentifier": "hsap_genome_rsrc",
               "resourceVersion": "2.6",
               "resourceDisplayName": "human genome"}
              ],
           "projects": ["PlasmoDB"],
           "owner": userId,
           "size": size,
           "modified": timestamp,
           "created": timestamp
        }, datasetFile, indent=4)

    # The result file contains the information to be returned to the Galaxy user
    with open(results, "w+") as resultsFile:

        os.chdir(tempPath)

        fileRoot = "dataset_u" + userId + "_t" + str(timestamp)

        # Package the tarball using the dataset_uNNNNN_tNNNNN.tgz convention
        with tarfile.open(fileRoot + ".tgz", "w:gz") as tarball:
            for item in ["meta.json", "dataset.json", "datafiles"]:
                tarball.add(item)

        # Call the IRODS rest service to drop the tarball into the IRODS workspace landing zone
        restUrl = "http://wij.vm:8180/irods-rest/rest/fileContents/ebrc/workspaces/lz/" + fileRoot + ".tgz"
        headers = {"Accept":"application/json"}
        file = {"uploadFile":open(fileRoot + ".tgz","rb")}
        # TODO - POC only!! gotta salt away the usr/pwd somehow
        auth = HTTPBasicAuth('wrkspuser', 'passWORD')

        response = requests.post(restUrl, auth=auth, headers=headers, files=file)
        resultsFile.write("Tarball - " + str(response.status_code) + "\n" + response.text + "\n")

        # Call the IRODS rest service to drop a flag into the IRODS workspace landing zone.  This flag
        # triggers the IRODS PEP that unpacks the tarball and posts the event to Jenkins
        with open(fileRoot + ".txt", "w+") as flag:
            flag.write("flag")
        restUrl = "http://wij.vm:8180/irods-rest/rest/fileContents/ebrc/workspaces/lz/" + fileRoot + ".txt"
        file = {"uploadFile": open(fileRoot + ".txt", "rb")}
        response = requests.post(restUrl, auth=auth, headers=headers, files=file)
        resultsFile.write("Flag - " + str(response.status_code) + "\n" + response.text + "\n")

        # TODO - throw away the temp dir.
        resultsFile.write("The temporary dataset directory is " + tempPath)




if __name__ == "__main__": __main__()