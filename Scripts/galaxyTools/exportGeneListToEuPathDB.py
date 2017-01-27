# !/usr/bin/env python

import eupath_genelist_exporter
import eupath_exporter
import optparse
import sys
import os


def main():
    """
      The following program is a Galaxy Tool for exporting gene list data from Galaxy to EuPathDB via iRODS.

      Sample for testing outside of Galaxy:
      python exportGeneListToEuPathDB.py
             "a name" "a summary" "a description" "test-data/genelist.txt" "108976930" <this directory>
    """

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    # Salt away all parameters.
    dataset_name = args[0]
    summary = args[1]
    description = args[2]
    dataset_file_path = args[3]
    #user_id = args[4]
    # My WDK user id for now
    user_id = "108976930"
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
        sys.exit(os.EX_DATAERR)


if __name__ == "__main__":
    sys.exit(main())