# This action is called by the acPostProcForPut action where a tgz file is deposited in
# the landing zone for user datasets.  It takes the collection name and the data object name
# as inputs.  The data object name is expected in the form 'dataset_u\d+_t\d+.tgz'.
# The _u\d+ portion defines the user id and the _t\d+ is a timestamp or some other
# mechanism for making the file unique.  The tarball is unpacked in /ebrc/workspaces/users/<userId>/datasets<datasetId>
# where the userId is extracted from the tarball name and the dataset id is the data id given by irods to this particular file.
acLandingZonePostProcForPut(*fileDir, *fileName) {
	*userId = trimr(triml(*fileName,"_u"),"_t");  #expect file name in format dataset_u\d+_t\d+.tgz
	*dataObjectIds = SELECT DATA_ID WHERE DATA_NAME = *fileName AND COLL_NAME = *fileDir;
	*datasetId = "";
	foreach(*dataObjectId in *dataObjectIds) {
	  *datasetId = *dataObjectId.DATA_ID;
    }
    *userDatasetPath = "/ebrc/workspaces/users/*userId/datasets/*datasetId";
  	msiTarFileExtract($objPath, *userDatasetPath, $rescName, *UpStatus);
    writeLine("serverLog", "Unpacked $objPath to *userDatasetPath");
}



