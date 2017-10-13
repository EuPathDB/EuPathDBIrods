# !/usr/bin/env python

import eupath_genelist_exporter
import eupath_exporter
import optparse
import sys
import re


def main():
    """
      The following program is a Galaxy Tool for exporting gene list data from Galaxy to EuPathDB via iRODS.

      Sample for testing outside of Galaxy:
      python exportGeneListToEuPathDB.py
             "a name" "a summary" "a description" "test-data/genelist.txt" "<user.wdk_id@eupath.org>" <this directory>
    """

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    # Salt away all parameters.
    if len(args) < 5:
        raise eupath_exporter.ValidationException("The tool was passed an insufficient numbers of arguments.")
    dataset_name = args[0]
    summary = args[1]
    description = args[2]
    dataset_file_path = args[3]
    user_email = args[4].strip()
    if not re.match(r'.+\.\d+@eupathdb.org$', user_email, flags=0):
        raise eupath_exporter.ValidationException("The user email " + str(user_email) + " is not valid for the use of this tool.")
    galaxy_user = user_email.split("@")[0]
    user_id = galaxy_user[galaxy_user.rfind(".") + 1:]
    tool_directory = args[5]

    reference_genome = "This is a ref genome for now"

    # Create and populate the meta.json file that must be included in the tarball
    exporter = eupath_genelist_exporter.GeneListExport(dataset_file_path,
                                                       reference_genome,
                                                       user_id,
                                                       dataset_name,
                                                       summary,
                                                       description,
                                                       tool_directory)
    try:
        exporter.export()
    except eupath_exporter.ValidationException as ve:
        print str(ve)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())