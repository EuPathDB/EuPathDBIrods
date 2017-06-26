#!/bin/env python

import jenkins
import yaml
import sys
from optparse import OptionParser

def main():

    usage = """usage: %prog [options] dataset_id

This script takes a dataset_id and triggers a jenkins job with that id as a
parameter.  The jenkins configuation for connection and authentication are found
in /var/lib/irods/jenkins.conf
"""

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="store_true", default=False)

    (options, args) = parser.parse_args()

    if options.verbose:
        print options, args

    if len(args) != 1:
        parser.error("incorrect number of arguments")

    dataset_id = args[0]
    conf = get_conf()

    if options.verbose:
        print conf

    # gather params to send in to job
    params = {"DATASET_STORE_ID": dataset_id, "token": conf['job_token']}

    # setup jenkins server connection
    server = jenkins.Jenkins(conf['url'], username=conf['user'], password=conf['api_token'])

    # build job
    server.build_job(conf['job'], params)


def get_conf():
    """ Returns configuration values taken from conf file, or later on, some
    central store"""

    with open("/var/lib/irods/jenkins.conf", 'r') as stream:
        try:
            conf = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(-1)
    return conf


if __name__ == "__main__":
        sys.exit(main())

