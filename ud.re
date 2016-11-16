# -------------------- PEP Overrides ----------------- #

# Custom event hook for user dataset post processiong following an iput
acPostProcForPut {
	writeLine("serverLog", "PEP acPostProcForPut - $objPath");
	msiSplitPath($objPath, *fileDir, *fileName);
	# if a tgz file is put into the landing zone, unpack it
	if(*fileDir == "/ebrc/workspaces/lz" && *fileName like regex "dataset_u.*_t.*[.]tgz") then {
		acLandingZonePostProcForPut(*fileDir, *fileName);
	}
}

# Custom event hook for user dataset post processiong following an irm of a collection
acPostProcForRmColl {
    writeLine("serverLog", "PEP acPostProcForRmColl - $collName");
	if($collName like regex "/ebrc/workspaces/users/.*/datasets/.*") {
	  acDatasetPostProcForRmColl();
	}
}

acPostProcForCreate {
  writeLine("serverLog", "PEP acPostProceForCreate - $objPath");
  msiSplitPath($objPath, *fileDir, *fileName);
  if(*fileDir like regex "/ebrc/workspaces/users/.*/datasets/.*" && *fileName == ".install") then {
    acDatasetInstallPostProcForPut(*fileDir);
  }
}

# -------------------- Supporting Actions ----------------- #

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
	  writeLine("serverLog", "Unpacking $objPath to *userDatasetPath");
  	  msiTarFileExtract($objPath, *userDatasetPath, $rescName, *UnpkStatus):::msiDataObjUnlink("objPath=$objPath++++replNum=0++++forceFlag=",*DelStatus);
	  writeLine("serverLog", "Unpacked $objPath successfully");
	  
	  *installDataObj = "*userDatasetPath/.install"; 
	  msiDataObjCreate(*installDataObj,"destRescName=$rescName",*installFileDescriptor);
	  msiDataObjClose(*installFileDescriptor,*installStatus);
	  
	  # remove the tarball following unpacking.
	  msiDataObjUnlink("objPath=$objPath++++replNum=0++++forceFlag=",*DelStatus);
	  writeLine("serverLog", "Removed $objPath tarball");
    }
	else {
	  # file name is mis-formatted, so toss.	
	  msiDataObjUnlink("objPath=$objPath++++replNum=0++++forceFlag=",*DelStatus);
	}
}


acDatasetInstallPostProcForPut(*fileDir) {
  msiSplitPath(*fileDir, *parentDir, *datasetId);
  writeLine("serverLog", "Responding to an install of *datasetId");
  acCreateEventContentForUnpack(*fileDir, *datasetId, *content);
  acPostEvent(*content);
}

# This rule posts the content provided to a new event data object in the events
# collection.  The use of systemTime in the event data object name may not be sufficient
# to insure uniqueness.  May need to obtain something from the caller to help insure that.
acPostEvent(*eventContent) {
  msiGetIcatTime(*systemTime,"unix");
  *fileName = "event_*systemTime.txt";
  *eventPath = "/ebrc/workspaces/events/*fileName";
  msiDataObjCreate(*eventPath,"destRescName=$rescName",*eventFileDescriptor);
  msiDataObjWrite(*eventFileDescriptor,*eventContent,*fileLength);
  msiDataObjClose(*eventFileDescriptor,*eventStatus);
  writeLine("serverLog", "Created event file *fileName");
}	


# Called once a dataset tarball is unpacked and placed in the owner's collection.  Reads the
# accompanying dataset.json data object, calls a python script the parse the json into a more
# digestable format and returns the data according to the following tab delimited format:
# content: 'install' projects user_dataset_id ud_type_name ud_type_version owner_user_id dependency dependency_version
acCreateEventContentForUnpack(*userDatasetPath, *datasetId, *content) {
	*DatasetConfigPath = "*userDatasetPath/dataset.json";
	*results = SELECT DATA_SIZE WHERE COLL_NAME = *userDatasetPath AND DATA_NAME = 'dataset.json';
	*fileSize = 0;
	foreach(*results) {
		*fileSize = *results.DATA_SIZE;
	}
	writeLine("serverLog", "File size: *fileSize");
	msiDataObjOpen("objPath=*DatasetConfigPath++++rescName=$rescName++++replNum=0++++openFlags=O_RDONLY", *fileDescriptor);
	msiDataObjRead(*fileDescriptor,*fileSize,*datasetData);
	# Escapes the double quotes so that the content is transmitted as an intact single string.
	*DatasetDataArg = execCmdArg(str(*datasetData));
	msiDataObjClose(*fileDescriptor,*closeStatus);
	msiExecCmd("datasetParser.py", *DatasetDataArg,"null","null","null",*Result);
	msiGetStdoutInExecCmdOut(*Result,*Out);
	msiString2KeyValPair(*Out, *pairs);
	*content = "install\tnull\t*datasetId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\t" ++ *pairs.owner_user_id ++ "\t" ++ *pairs.dependency ++ "\t" ++ *pairs.dependency_version ++ "\n";
	writeLine("serverLog", *content);
}

acDatasetPostProcForRmColl() {
	writeLine("serverLog", "Need to fire off an event");
}