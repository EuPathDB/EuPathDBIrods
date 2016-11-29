#!/usr/bin/env python

import sys
import subprocess

# "wrkspuser,7c88562ca511b8bbbf18055c961f24a0,http://ies.irods.vm:8080/job/HelloWorld/build?token=thisisatest
# http://ies.irods.vm:8080/job/HelloWorld/build?token=thisisatest"

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