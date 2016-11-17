# This file goes in /etc/irods (need sudo).  Reference to it is made in
# /etc/irods/server_config.json (need sudo) as follows:
# "re_rulebase_set": [{"filename": "ud"},{"filename":"core"}] there could be other rule sets

# -------------------- PEP Overrides ----------------- #

# Custom event hook for user dataset post processiong following an iput
acPostProcForPut {
	writeLine("serverLog", "PEP acPostProcForPut - $objPath");
	msiSplitPath($objPath, *fileDir, *fileName);
	# if a tgz file is put into the landing zone, unpack it
	if(*fileDir == "/ebrc/workspaces/lz" && *fileName like regex "dataset_u.*_t.*[.]tgz") then {
		acLandingZonePostProcForPut(*fileDir, *fileName);
	}
#	else if(*fileDir like regex "/ebrc/workspaces/users/.*/deletedDatasets/*" && *fileName == 'dataset.json') then {
#		acDatasetDeletionPostProcForPut(*fileDir);
#	}
}

# Custom event hook for user dataset post processiong following an irm of a collection
acPreprocForRmColl {
    writeLine("serverLog", "PEP acPreprocForRmColl - $collName");
	if($collName like regex "/ebrc/workspaces/users/.*/datasets/.*") {
	  acDatasetPreprocForRmColl();
	}
}

acPostProcForCreate {
  writeLine("serverLog", "PEP acPostProcForCreate - $objPath");
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
	  
	  # Remove the tarball following unpacking.
	  msiDataObjUnlink("objPath=$objPath++++replNum=0++++forceFlag=",*DelStatus);
	  writeLine("serverLog", "Removed $objPath tarball");
	  
	  # Fabricate an event.
	  acGetDatasetJsonContent(*userDatasetPath, *pairs)
	  *content = "install\t" ++ *pairs.projects ++ "\t$dataId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\t" ++ *pairs.owner_user_id ++ "\t" ++ *pairs.dependency ++ "\t" ++ *pairs.dependency_version ++ "\n";
	  acPostEvent(*content);
    }
	else {
	  # file name is mis-formatted, so toss.	
	  msiDataObjUnlink("objPath=$objPath++++replNum=0++++forceFlag=",*DelStatus);
	}
}


# This rule posts the content provided to a new event data object in the events
# collection.  The use of systemTime in the event data object name may not be sufficient
# to insure uniqueness.  May need to obtain something from the caller to help insure that.
# Since iRODS microservices only return timestamps in seconds, we are resorting to a
# python call to get the timestamp in milliseconds (could have been a shell call)
acPostEvent(*eventContent) {
  msiExecCmd("produceTimestamp.py","null","null","null","null",*Result);
  msiGetStdoutInExecCmdOut(*Result,*Out)
  *fileName = "event_*Out.txt";
  *eventPath = "/ebrc/workspaces/events/*fileName";
  msiDataObjCreate(*eventPath,"null",*eventFileDescriptor);
  msiDataObjWrite(*eventFileDescriptor,*eventContent,*fileLength);
  msiDataObjClose(*eventFileDescriptor,*eventStatus);
  writeLine("serverLog", "Created event file *fileName");
}	

# Called before a dataset is removed.  Reads and parses the dataset.json to get the data needed to create
# an event data object.  The single line posted to the event object is composed as follows:
# content:  uninstall projects user_dataset_id ud_type_name ud_type_version
acDatasetPreprocForRmColl() {
	msiSplitPath($collName, *parent, *datasetId);
	acGetDatasetJsonContent($collName, *pairs);
	*content = "uninstall\t" ++ *pairs.projects ++ "\t*datasetId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\n";
	acPostEvent(*content)
}

# Retrieves the dataset.json content in the form of key/value pairs that are digestable via the iRODS microservices.
# *userDatasetPath - input - absolute path to the dataset of interest (/ebrc/workspaces/users/<userid>/datasets/<datasetid)
# *content - output - a string containing key/value pairs
# In addition to the dataset.json content and system timestamp in milliseconds is returned to provide a unique identifier
# for any subsequent file holding this content
# TODO:  Perhaps the timestamp long int retrieval should be split off into a separate python script for separation of
# concerns.
acGetDatasetJsonContent(*userDatasetPath, *content) {
	*DatasetConfigPath = "*userDatasetPath/dataset.json";
	*results = SELECT DATA_SIZE WHERE COLL_NAME = *userDatasetPath AND DATA_NAME = 'dataset.json';
	*fileSize = 0;
	foreach(*results) {
	  *fileSize = *results.DATA_SIZE;
	}
	writeLine("serverLog", "File size: *fileSize");
	writeLine("serverLog", "Dataset conf path is *DatasetConfigPath");
	msiDataObjOpen("objPath=*DatasetConfigPath++++replNum=0++++openFlags=O_RDONLY", *fileDescriptor);
	msiDataObjRead(*fileDescriptor,*fileSize,*datasetData);
	# Escapes the double quotes so that the content is transmitted as an intact single string.
	*DatasetDataArg = execCmdArg(str(*datasetData));
	msiDataObjClose(*fileDescriptor,*closeStatus);
	msiExecCmd("datasetParser.py", *DatasetDataArg,"null","null","null",*Result);
	msiGetStdoutInExecCmdOut(*Result,*Out);
	msiString2KeyValPair(*Out, *content);
}