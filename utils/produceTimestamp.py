#!/usr/bin/env python

import sys
import time

# Utility return a string version of a current datetime in milliseconds starting from the epoch
# iRODS currently only supplies a current datetime in seconds.

def main():
  sys.stdout.write(str(int(time.time() * 1000)))

if __name__ == "__main__":
    sys.exit(main())
