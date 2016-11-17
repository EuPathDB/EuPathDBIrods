#!/usr/bin/env python

import sys
import json

# Utility to parse the dataset.json file accompanying a dataset and to
# return the content in the form of a string that can be parsed by the
# calling rule.


# '{ "type": {"name": "RNA Seq", "version": "1.0"},"dependencies": [{"resourceIdentifier": "pf3d7_genome_rsrc",  "resourceVersion": "12/2/2015", "resourceDisplayName": "pfal genome"},  {"resourceIdentifier": "hsap_genome_rsrc",    "resourceVersion": "2.6",   "resourceDisplayName": "human genome"} ],"projects":["PlasmoDB","FungiDB"],"owner": 12345,"size": "200M","modified": 1248312231083,"created": 1231238088881,"uploaded": 1231398508344}'


def main():
  args = sys.argv[1:]
  if len(args) == 0:
    raise IOError("A well-formed json string is required.")
#  rawJson = ''.join(args).replace('\n','')  Newlines don't seem to be a problem in iRODS
  parsedJson = json.loads(args[0])
  type = parsedJson['type']
  dependencies = parsedJson['dependencies']
  projects = ",".join(parsedJson['projects'])
  output = "projects=" + projects + "%" + \
           "owner_user_id=" + str(parsedJson['owner']) + "%" + \
           "ud_type_name=" + type['name'] + "%" + \
           "ud_type_version=" + type['version'] + "%" + \
           "dependency=" + dependencies[0]['resourceIdentifier'] + "%" + \
           "dependency_version=" + dependencies[0]['resourceVersion']
  sys.stdout.write(output)

if __name__ == "__main__":
    sys.exit(main())
