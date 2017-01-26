# !/usr/bin/env python

import eupath_genelist_exporter
import optparse


def __main__():
    """
      The following program is a Galaxy Tool for exporting gene list data from Galaxy to EuPathDB via IRODS.

      Sample for testing outside of Galaxy:
      python exportGeneListToEuPathDB.py
             "a name" "a summary" "a description" "test-data/genelist.txt" "test-data/output.txt" "108976930"
    """

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    # Salt away all parameters.
    dataset_name = args[0]
    summary = args[1]
    description = args[2]
    dataset_file_path = args[3]
    status_file = args[4]
    #user_id = args[5]
    # My WDK user id for now
    user_id = "108976930"

    reference_genome = "This is a ref genome for now"


    # Create and populate the meta.json file that must be included in the tarball
    exporter = eupath_genelist_exporter.GeneListExport(dataset_file_path,
                                                       reference_genome,
                                                       user_id,
                                                       dataset_name,
                                                       summary,
                                                       description,
                                                       status_file)
    exporter.export()


if __name__ == "__main__": __main__()