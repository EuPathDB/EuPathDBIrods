#!/usr/bin/python

import eupath_exporter


class GeneListExport(eupath_exporter.Export):
    """
    This class is a specialized version of the Galaxy to EuPathDB dataset export tool.  This tool's
    specialty is furnishing user's gene list data to EuPathDB.  As with all specialty export tools, this
    tool implements 3 abstract classes.
    """

    # Name given to this type of dataset and to the expected file
    GENE_LIST_TYPE = "GeneList"
    GENE_LIST_VERSION = "1.0"
    GENE_LIST_FILE = "genelist.txt"

    # The validation script to be applied to the dataset files.  A failed validation should
    # return in a system exit status of other than 0.
    GENE_LIST_VALIDATION_SCRIPT = "validate_gene_list.py"

    def __init__(self, dataset_file_path, reference_genome, *args):
        """
        Initializes the gene list export class with the parameters needed to accomplish the particular
        type of export.
        :param dataset_file_path: The location in Galaxy of the gene list file
        :param reference_genome: The reference genome to use
        :param args: These args are needed by the generic EuPathDB export tool
        """
        eupath_exporter.Export.__init__(self,
                                        GeneListExport.GENE_LIST_TYPE,
                                        GeneListExport.GENE_LIST_VERSION,
                                        GeneListExport.GENE_LIST_VALIDATION_SCRIPT,
                                        *args)
        self._dataset_file_path = dataset_file_path
        self._reference_genome = reference_genome

    def identify_dependencies(self):
        """
        The gene list is expected not to have any dependencies.  So an empty list is sufficient here.
        :return: []
        """
        return [{"resourceIdentifier": "pf3d7_genome_rsrc",
                 "resourceVersion": "12/2/2015",
                 "resourceDisplayName": "pfal genome"},
                {"resourceIdentifier": "hsap_genome_rsrc",
                 "resourceVersion": "2.6",
                 "resourceDisplayName": "human genome"}]

    def identify_projects(self):
        """
        The appropriate project will be determined by DD.  Note that the string returned should
        follow the convention for a Eupath project - first letter and DB suffix in uppercase
        (e.g., PlasmoDB, ToxoDB).
        :return: list containing the single relevant EuPath project
        """
        return ["PlasmoDB"]

    def identify_dataset_files(self):
        """
        The user provided gene list file is combined with the name EuPathDB expects
        for such a file
        :return: A list containing the single dataset file accompanied by its EuPathDB designation.
        """
        return [{"name": self.GENE_LIST_FILE, "path": self._dataset_file_path}]
