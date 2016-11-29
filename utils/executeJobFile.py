#!/usr/bin/env python

import sys
from subprocess import call

def main():
  args = sys.argv[1:]
  if len(args) != 1:
    raise IOError("Expected a single string argument containing job file path, username, and password separated with commas.")
  paramString = "".join(args);
  params = "".join(args).split(",")
  username = params[0]
  password = params[1]
  jobData = params[2].split("\n")
  preamble = "wget --auth-no-challenge --http-user=" + username + " --http-password=" + password + " "
  for url in jobData:
    cmd = preamble + url + "\n"
    sys.stdout.write(cmd)
    call(cmd, shell=True)
  sys.stdout.write("Complete")
  
if __name__ == "__main__":
    sys.exit(main())  