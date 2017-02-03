# !/usr/bin/env python
import optparse
from subprocess import Popen, PIPE
import os
import sys
import json
from os.path import expanduser


def main():
    """
    Utility intended to flush development iRODS and development ApiDBUserDatasets schemas.  Removes iRODS contents of
    the iRODS collections lz, events and flags.  Also removes dataset collections from staging and from each user's
     datasets folder (with a flag set to prevent PEP acPreprocForRmColl from doing anything significant).  Only the
    data tables so far used are flushed.  More may be needed later.
    """
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    usr = "ApidbUserDatasets"
    pwd = args[0]
    credentials = "%s/%s" % (usr, pwd)
    dbs = ['toxo-inc', 'plas-inc']

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
    utility_file_folder = os.environ['PROJECT_HOME'] + "/EuPathDBIrods/Scripts/utilityRules"

    # Assuming this irods is hosted via vagrant on wij.vm
    if get_irods_host_from_env() != "wij.vm":
        raise Exception("This flush intended ONLY for wij.vm")

    rule = "%s/%s" % (utility_file_folder, "emptyLandingZoneCollection.r")
    session = Popen(['irule', '-F', rule])
    print session.communicate()

    rule = "%s/%s" % (utility_file_folder, "emptyFlagsCollection.r")
    session = Popen(['irule', '-F', rule])
    print session.communicate()

    rule = "%s/%s" % (utility_file_folder, "emptyStagingCollection.r")
    session = Popen(['irule', '-F', rule])
    print session.communicate()

    rule = "%s/%s" % (utility_file_folder, "deleteDatasets.r")
    session = Popen(['irule', '-F', rule])
    print session.communicate()

    # This must run after the other rules because the act of deleting datasets spawns events
    rule = "%s/%s" % (utility_file_folder, "emptyEventsCollection.r")
    session = Popen(['irule', '-F', rule])
    print session.communicate()

    for db in dbs:
        for sql_cmd in sql_cmds:
            print sql_cmd
            session = Popen(['sqlplus', '-S', credentials + "@" + db], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            session.stdin.write(sql_cmd)
        print session.communicate()


def get_irods_host_from_env():
    """
    Obtain the iRODS host from the user's iRODS environment file
    :return: iRODS host
    """
    home = expanduser("~")
    irods_env_filename = home + "/.irods/irods_environment.json"
    with open(irods_env_filename, "r") as irods_env_file:
        irods_env_json = irods_env_file.read()
        irods_env = json.loads(irods_env_json)
        return irods_env['irods_host']


if __name__ == "__main__":
    sys.exit(main())
