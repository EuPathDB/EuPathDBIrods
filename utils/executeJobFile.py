#!/usr/bin/env python

import sys
import subprocess

# Utility method to take output of jobFile.txt (sent via IRODS), turn it into a series of wgets using the
# username and password provided via IRODS.  Each wget is called in turn.  Example argument for testing is
# provided below (see sure to remove hashes and any spurious characters the editor may introduce)

# "wrkspuser,7c88562ca511b8bbbf18055c961f24a0,http://ies.irods.vm:8080/job/SanityTest/build?token=sanitytest
# http://ies.irods.vm:8080/job/HelloWorld/build?token=helloworldtest"

# This program resides in /var/lib/irods/iRODS/server/bin/cmd and is set as owned by wrkspuser.

def main():
  args = sys.argv[1:]
  if len(args) != 1:
    raise IOError("Expected a single string argument containing job file path, username, and password separated with commas.")
  params = "".join(args).split(",")
  username = params[0]
  password = params[1]
  jobData = params[2].split("\n")
  preamble = "wget --quiet --auth-no-challenge --http-user=" + username + " --http-password=" + password + " "
  for url in jobData:
    cmd = preamble + url + "\n"
    sys.stdout.write(cmd)
    result = subprocess.check_call(cmd, shell=True)
    sys.stdout.write("Result:" + str(result) + "\n")
  sys.stdout.write("Complete")
  
if __name__ == "__main__":
    sys.exit(main())  