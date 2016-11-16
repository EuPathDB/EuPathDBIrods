#!/usr/bin/env python

import sys
import json

# Utility to parse the dataset.json file accompanying a dataset and to
# return the content in the form of a string that can be parsed by the
# calling rule.
def main():
  args = sys.argv[1:]
  if len(args) == 0:
    raise IOError("A well-formed json string is required.")
  rawJson = ''.join(args).replace('\n','')
  parsedJson = json.loads(args[0])
  type = parsedJson['type']
  dependencies = parsedJson['dependencies']
  output = "owner_user_id=" + type['owner'] + "%" + "ud_type_name=" + type['name'] + "%" + "ud_type_version=" + type['version'] + "%" + "dependency=" + dependencies[0]['resourceIdentifier'] + "%" + "dependency_version=" + dependencies[0]['resourceVersion']
  sys.stdout.write(output)

if __name__ == "__main__":
    sys.exit(main())
