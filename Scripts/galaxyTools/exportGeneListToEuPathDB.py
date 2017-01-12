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

# Sample for testing outside of Galaxy:
# python exportGeneListToEuPathDB.py "a name" "a description" "a summary" "test-data/genelist.txt" "test-data/output.txt" "108976930"

def __main__():

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    timestamp = int(time.time() * 1000)

    datasetName = args[0]
    description = args[1]
    summary = args[2]
    datasetFiles = args[3]
    results = args[4]
    userId = args[5]
    # My WDK user id for now
    userId = "108976930"

    tempPath = tempfile.mkdtemp('dataset_u' + userId + '_t' + str(timestamp))
    os.mkdir(tempPath + "/datafiles")

    path, name = os.path.split(datasetFiles)

    # Must datafiles have specific names?
    shutil.copy(datasetFiles, tempPath + "/datafiles/genelist.txt")

    with open(tempPath + "/meta.json", "w+") as metaFile:
        dump({'name': datasetName,
              'description': description,
              'summary': summary}, metaFile, indent=4)

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
           "size": 200000000,
           "modified": timestamp,
           "created": timestamp
        }, datasetFile, indent=4)

    with open(results, "w+") as resultsFile:

        os.chdir(tempPath)

        fileRoot = "dataset_u" + userId + "_t" + str(timestamp)


        with tarfile.open(fileRoot + ".tgz", "w:gz") as tarball:
            for item in ["meta.json", "dataset.json", "datafiles"]:
                tarball.add(item)

        restUrl = "http://wij.vm:8180/irods-rest/rest/fileContents/ebrc/workspaces/lz/" + fileRoot + ".tgz"
        headers = {"Accept":"application/json"}
        file = {"uploadFile":open(fileRoot + ".tgz","rb")}
        auth = HTTPBasicAuth('wrkspuser', 'passWORD')

        response = requests.post(restUrl, auth=auth, headers=headers, files=file)
        resultsFile.write("Tarball - " + str(response.status_code) + "\n" + response.text + "\n")

        with open(fileRoot + ".txt", "w+") as flag:
            flag.write("flag")
        restUrl = "http://wij.vm:8180/irods-rest/rest/fileContents/ebrc/workspaces/lz/" + fileRoot + ".txt"
        file = {"uploadFile": open(fileRoot + ".txt", "rb")}
        response = requests.post(restUrl, auth=auth, headers=headers, files=file)
        resultsFile.write("Flag - " + str(response.status_code) + "\n" + response.text + "\n")

        resultsFile.write("The temporary dataset directory is " + tempPath)




if __name__ == "__main__": __main__()