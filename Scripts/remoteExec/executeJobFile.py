#!/usr/bin/env python

import sys
import subprocess
from urlparse import urlparse
import time

# Utility method to take output of jobFile.txt (sent via IRODS), turn it into a series of wgets using the
# username and password provided via IRODS.  Each wget is called in turn.  Example argument for testing is
# provided below (see sure to remove hashes and any spurious characters the editor may introduce)

# "wrkspuser,be4797e4b88200492d29cf0aeb32f5de,http://wij.vm:9171/job/IrodsListener/buildWithParameters?token=eupathdbirods,PlasmoDB"

# This program resides in /var/lib/irods/iRODS/server/bin/cmd and is set as owned by wrkspuser.

def main():
  args = sys.argv[1:]
  if len(args) != 1:
    raise IOError("Expected a single string argument containing job file path, username, and password separated with commas.")
  params = "".join(args).split(",")
  username = params[0]
  password = params[1]
  jobUrl = params[2]
  jenkinsHost = urlparse(jobUrl).hostname + ":" + str(urlparse(jobUrl).port)
  jobParams = params[3].split("\n")
  preamble = "wget  --quiet --auth-no-challenge --http-user=" + username + " --http-password=" + password + " "
  crumbRequest = preamble + "--output-document - '" + jenkinsHost + "/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)'"
  #sys.stdout.write(crumbRequest)
  requestCrumb = subprocess.Popen(crumbRequest, shell=True, stdout=subprocess.PIPE)
  requestCrumb.wait()
  crumb = str(requestCrumb.communicate()[0])
  header = "--header='" + crumb + "'"
  for jobParam in jobParams:
    if len(jobParam) > 0:
      time.sleep(30)
      cmd = preamble + " " + header + "--post-data=\"PROJECT_ID=" + jobParam + "\" " + jobUrl + "\n"
      sys.stdout.write(cmd)
      requestEvents = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
      requestEvents.wait()
      result = str(requestEvents.communicate())
      #sys.stdout.write("Result:" + result + "\n")
  sys.stdout.write("Complete")
  
if __name__ == "__main__":
    sys.exit(main())  