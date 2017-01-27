# This file goes in /etc/irods (need sudo).  Reference to it is made in
# /etc/irods/server_config.json (need sudo) as follows:
# "re_rulebase_set": [{"filename": "ud"},{"filename":"core"}] there could be other rule sets

# -------------------- PEP Overrides ----------------- #

# Custom event hook for user dataset post processiong following an iput
acPostProcForPut {
	writeLine("serverLog", "PEP acPostProcForPut - $objPath");
	msiSplitPath($objPath, *fileDir, *fileName);
	# if a properly composed txt file is put into the landing zone, find the corresponding tarball and upack it.
	if(*fileDir == "/ebrc/workspaces/flags" && *fileName like regex "dataset_u.*_t.*[.]txt") then {
		*tarballName = trimr(*fileName,".") ++ ".tgz";
		acLandingZonePostProcForPut("/ebrc/workspaces/lz", *tarballName);
	}
	# if a file is put into the sharedWith directory of a dataset, report it
	else if(*fileDir like regex "/ebrc/workspaces/users/.*/datasets/.*/sharedWith") then {
		acSharingPostProcForPutOrDelete(*fileDir, *fileName, "grant");
	}
	else if(*fileDir like regex "/ebrc/workspaces/users/.*/externalDatasets") then {
		acExternalPostProcForPutOrDelete(*fileDir, *fileName, "create")
	}
}

# Custom event hook for determining what can be deleted 
acDataDeletePolicy {
	writeLine("serverLog", "PEP acDataDeletePolicy - $objPath");
}

# Custom event hook for user dataset post processing following the irm of a data object
# Note that this event hook responds to irm -f only.  
acPostProcForDelete {
    writeLine("serverLog", "PEP acPostProcForDelete - $objPath");
	msiSplitPath($objPath, *fileDir, *fileName);
	if(*fileDir like regex "/ebrc/workspaces/users/.*/datasets/.*/sharedWith") then {
		acSharingPostProcForPutOrDelete(*fileDir, *fileName, "revoke");
	}
	else if(*fileDir like regex "/ebrc/workspaces/users/.*/externalDatasets") then {
		acExternalPostProcForPutOrDelete(*fileDir, *fileName, "delete")
	}
}

# Custom event hook for user dataset pre-processiong preceeding an irm of a collection
acPreprocForRmColl {
    writeLine("serverLog", "PEP acPreprocForRmColl - $collName");
    *FlushFilePath = "/ebrc/workspaces/flushMode";
    msiDataObjOpen("objPath=*FlushFilePath++++replNum=0++++openFlags=O_RDONLY", *flushFileDescriptor);
    if(flushFileDescriptor < 0 && $collName like regex "/ebrc/workspaces/users/.*/datasets/.*") {
	  acDatasetPreprocForRmColl();
	}
}

acPostProcForCreate {
  writeLine("serverLog", "PEP acPostProcForCreate - $objPath");
}

# -------------------- Supporting Actions ----------------- #

# This action is called by the acPostProcForPut action whenever a tgz file is deposited in
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
	  *tarballPath = *fileDir ++ "/" ++ *fileName;
      *userDatasetPath = "/ebrc/workspaces/users/*userId/datasets/$dataId";
	  writeLine("serverLog", "Unpacking $objPath to *userDatasetPath");
  	  msiTarFileExtract(*tarballPath, *userDatasetPath, $rescName, *UnpkStatus);
	  writeLine("serverLog", "Unpacked *tarballPath successfully");

	  # Fabricate an event.
	  acGetDatasetJsonContent(*userDatasetPath, *pairs)
	  
	  # Add the uploaded timestamp to the dataset.json data object belonging to the newly added dataset
	  acOverwriteDatasetJsonContent(*userDatasetPath, *pairs.modifiedContent);

	  # Assemble the line to be posted as an event and post it
	  *content = "install\t" ++ *pairs.projects ++ "\t$dataId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\t" ++ *pairs.owner_user_id ++ "\t" ++ *pairs.dependency ++ " " ++ *pairs.dependency_version ++ "\n";
	  acPostEvent(*content);

	  # Remove the tarball only if everything succeeds
	  msiDataObjUnlink("objPath=*tarballPath++++replNum=0++++forceFlag=",*DelStatus);
	  writeLine("serverLog", "Removed *tarballPath tarball");
    }
	else {
	  # file name is mis-formatted, so toss and email error report.
	  msiSendMail("criswlawrence@gmail.com","IRODS acPostProcForPut","The tarball filename, *fileName was mis-formatted.  No event was posted.");
	}
}

# This action is called by the acPostProcForPut action whenever a data object with a name corresponding to a share
# recipient is put into a dataset's sharedWith collection or removed from it.  The action creates an event in the events
# folder with the following tab-delimited data:
# share projects user_dataset_id ud_type_name ud_type_version user_id grant or revoke
acSharingPostProcForPutOrDelete(*fileDir, *recipientId, *action) {
  msiSplitPath(*fileDir, *userDatasetPath, *trash);
  writeLine("serverLog", "User dataset is *userDatasetPath");
  msiSplitPath(*userDatasetPath, *parent, *datasetId);
  writeLine("serverLog", "Recipient is *recipientId and Dataset is *datasetId");
  
  # Fabricate a share event.
  acGetDatasetJsonContent(*userDatasetPath, *pairs)
  *content = "share\t" ++ *pairs.projects ++ "\t*datasetId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\t" ++ *recipientId ++ "\t" ++ *action ++ "\n";
  acPostEvent(*content);
}

# externalDataset projects user_dataset_id ud_type_name ud_type_version user_id create/delete
acExternalPostProcForPutOrDelete(*fileDir, *fileName, *action) {
	*ownerId = trimr(*fileName,".");  # expected fileName in the form ownerId.externalDatasetId
	*externalDatasetId = triml(*fileName,".");
	writeLine("serverLog", "Owner id is *ownerId and External Dataset id is *externalDatasetId");
	
    # Fabricate an external dataset event.
	*ownerDatasetPath = "/ebrc/workspaces/users/*ownerId/datasets/*externalDatasetId"; 
    acGetDatasetJsonContent(*ownerDatasetPath, *pairs)
    *content = "externalDataset\t" ++ *pairs.projects ++ "\t*externalDatasetId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\t" ++ *ownerId ++ "\t" ++ *action ++ "\n";
    acPostEvent(*content);
}


# This rule posts the content provided to a new event data object in the events
# collection.  The use of systemTime in the event data object name may not be sufficient
# to insure uniqueness.  May need to obtain something from the caller to help insure that.
# Since iRODS microservices only return timestamps in seconds, we are resorting to a
# python call to get the timestamp in milliseconds (could have been a shell call)
acPostEvent(*eventContent) {
  msiExecCmd("produceTimestamp.py","null","null","null","null",*Result);
  msiGetStdoutInExecCmdOut(*Result,*Out);
  *fileName = "event_*Out.txt";
  *eventPath = "/ebrc/workspaces/events/*fileName";
  msiDataObjCreate(*eventPath,"null",*eventFileDescriptor);
  msiDataObjWrite(*eventFileDescriptor,*eventContent,*fileLength);
  msiDataObjClose(*eventFileDescriptor,*eventStatus);
  writeLine("serverLog", "Created event file *fileName");
  acTriggerEvent();
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

acOverwriteDatasetJsonContent(*userDatasetPath, *content) {
  writeLine("serverLog", "Need to overwrite dataset.json with *content");
  *DatasetConfigPath = "*userDatasetPath/dataset.json";
  msiDataObjOpen("objPath=*DatasetConfigPath++++replNum=0++++openFlags=O_RDWRO_TRUNC", *fileDescriptor);
  msiDataObjWrite(*fileDescriptor,*content,*fileSize);
  msiDataObjClose(*fileDescriptor,*fileStatus);
}

acTriggerEvent() {
	*jobFilePath = "/ebrc/workspaces";
	*jobFileName = "jenkinsCommunicationConfig.txt";
	*results = SELECT DATA_SIZE WHERE COLL_NAME = *jobFilePath AND DATA_NAME = *jobFileName;
	*fileSize = 0;
	foreach(*results) {
	  *fileSize = *results.DATA_SIZE;
	}
	writeLine("serverLog", "File size: *fileSize");
	msiDataObjOpen("objPath=*jobFilePath/*jobFileName++++replNum=0++++openFlags=O_RDONLY", *fileDescriptor);
	msiDataObjRead(*fileDescriptor,*fileSize,*jobData);
    *argv = str(*jobData);
	writeLine("serverLog", "Passing *argv");
    msiExecCmd("executeJobFile.py",*argv,"null","null","null",*Result);
    msiGetStdoutInExecCmdOut(*Result,*Out);
	writeLine("serverLog", *Out);
}