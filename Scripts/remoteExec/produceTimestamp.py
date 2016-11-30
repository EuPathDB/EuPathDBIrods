#!/usr/bin/env python

import sys
import time

# Utility return a string version of a current datetime in milliseconds starting from the epoch
# iRODS currently only supplies a current datetime in seconds.  This could probably be more simply
# done as a bash script.

# This program resides in /var/lib/irods/iRODS/server/bin/cmd and is set as owned by wrkspuser.

def main():
  sys.stdout.write(str(int(time.time() * 1000)))

if __name__ == "__main__":
    sys.exit(main())
