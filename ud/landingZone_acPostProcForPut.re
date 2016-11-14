# This action is called by the acPostProcForPut action where a tgz file is deposited in
# the landing zone for user datasets.  It takes the collection name and the data object name
# as inputs.  The data object name is expected in the form 'dataset_u\d+_t\d+.tgz'.
# The _u\d+ portion defines the user id and the _t\d+ is a timestamp or some other
# mechanism for making the file unique.  The tarball is unpacked in /ebrc/workspaces/users/<userId>/datasets<datasetId>
# where the userId is extracted from the tarball name and the dataset id is the data id given by irods to this particular file.
acLandingZonePostProcForPut(*fileDir, *fileName) {
	*userId = trimr(triml(*fileName,"_u"),"_t");  #expect file name in format dataset_u\d+_t\d+.tgz
	# insure the the user id is a positive number
	if(int(*userId) > 0) {
	  # unpack the tarball under the user datasets folder using the data id as the dataset id.	
      *userDatasetPath = "/ebrc/workspaces/users/*userId/datasets/$dataId";
  	  msiTarFileExtract($objPath, *userDatasetPath, $rescName, *UpStatus);
	  # remove the tarball following unpacking.
	  msiDataObjUnlink("objPath=$objPath++++replNum=0++++forceFlag=",*DepStatus);
      writeLine("serverLog", "Unpacked $objPath to *userDatasetPath");
    }
}



