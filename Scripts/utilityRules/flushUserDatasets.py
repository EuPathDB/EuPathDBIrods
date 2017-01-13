# !/usr/bin/env python
import optparse
from subprocess import Popen, PIPE
import os
import json
from os.path import expanduser

'''
Utility intended to flush development irods and development ApiDBUserDatasets schemas
'''
def __main__():
  parser = optparse.OptionParser()
  (options, args) = parser.parse_args()
  usr = "ApidbUserDatasets"
  pwd = args[0]
  credentials = "%s/%s" % (usr, pwd)
  dbs = ['toxo-inc','plas-inc']

  # For reasons unknown, the last cmd cannot terminate with a semicolon.
  sql_cmds = [
    'DELETE FROM USERDATASETEVENT;',
    'DELETE FROM UD_GENEID;',
    'DELETE FROM USERDATASETOWNER;',
    'DELETE FROM USERDATASETSHAREDWITH;',
    'DELETE FROM USERDATASETEXTERNALDATASET;',
    'DELETE FROM INSTALLEDUSERDATASET;',
    'COMMIT'
  ]

  # project home is required to find the utility irules
  if 'PROJECT_HOME' not in os.environ:
    raise Exception("PROJECT_HOME env variable must be set")
  utilityFileFolder = os.environ['PROJECT_HOME'] + "/EuPathDBIrods/Scripts/utilityRules"

  # Assuming this irods is hosted via vagrant on wij.vm
  if getIrodsHostFromEnv() != "wij.vm":
    raise Exception("This flush intended ONLY for wij.vm")


  rule = "%s/%s" % (utilityFileFolder, "emptyLandingZoneCollection.r")
  session = Popen(['irule','-F', rule])
  print session.communicate()

  rule = "%s/%s" % (utilityFileFolder, "deleteDatasets.r")
  session = Popen(['irule', '-F', rule])
  print session.communicate()

  # This must run after the other rules because the act of deleting datasets spawns events
  rule = "%s/%s" % (utilityFileFolder, "emptyEventsCollection.r")
  session = Popen(['irule', '-F', rule])
  print session.communicate()

  for db in dbs:

    for sql_cmd in sql_cmds:
      print sql_cmd
      session = Popen(['sqlplus', '-S', credentials + "@" + db], stdin=PIPE, stdout=PIPE, stderr=PIPE)
      session.stdin.write(sql_cmd)
    print session.communicate()

'''
Obtain the IRODS host from the user's IRODS environment file
'''
def getIrodsHostFromEnv():
  home = expanduser("~")
  irodsEnvFilename = home + "/.irods/irods_environment.json"
  with open(irodsEnvFilename, "r") as irodsEnvFile:
    irodsEnvJson = irodsEnvFile.read()
    irodsEnv = json.loads(irodsEnvJson)
    return irodsEnv['irods_host']






if __name__ == "__main__": __main__()