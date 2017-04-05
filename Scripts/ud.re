# This file goes in /etc/irods (need sudo).  Reference to it is made in
# /etc/irods/server_config.json (need sudo) as follows:
# "re_rulebase_set": [{"filename": "ud"},{"filename":"core"}] there could be other rule sets


# -------------------- PEP Overrides ----------------- #


# Custom event hook for user dataset post processiong following an iput
acPostProcForPut {
	writeLine("serverLog", "PEP acPostProcForPut - $objPath");
	*literals = getLiterals();
	msiSplitPath($objPath, *fileDir, *fileName);
	# if a properly composed txt file is put into the landing zone, find the corresponding tarball and upack it.
	writeLine("serverLog","File dir is *fileDir - does it match *literals.flagsPath");
	if(*fileDir == *literals.flagsPath && *fileName like regex "dataset_u.*_t.*[.]txt") then {
		*tarballName = trimr(*fileName,".") ++ ".tgz";
		acLandingZonePostProcForPut(*literals.landingZonePath, *tarballName);
	}
	# if a file is put into the external datasets directory of a recipient user, report it
	else if(*fileDir like regex "/ebrc/workspaces/users/.*/externalDatasets") then {
		acExternalPostProcForPutOrDelete(*fileDir, *fileName, "grant")
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
    *literals = getLiterals();
	msiSplitPath($objPath, *fileDir, *fileName);
	writeLine("serverLog", "File dir -  *fileDir and file name is *fileName");
	if(*fileDir like regex "/ebrc/workspaces/users/.*/externalDatasets") then {
		acExternalPostProcForPutOrDelete(*fileDir, *fileName, "revoke")
	}
}


# Custom event hook for user dataset pre-processiong preceding an irm of a collection
acPreprocForRmColl {
    writeLine("serverLog", "PEP acPreprocForRmColl - $collName");
    *exists = checkForDataObjectExistence('/ebrc/workspaces', 'flushMode')
    if(*exists) {
        writeLine("serverLog", "Flush mode in effect - exit PEP");
    }
    else {
        if($collName like regex "/ebrc/workspaces/users/.*/datasets/.*") {
	        acDatasetPreprocForRmColl();
	    }
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
# mechanism for making the file unique.  The tarball is subject to a limited validation and
# is unpacked first into a staging area.  If all goes well, the tarball is then unpacked in
# /ebrc/workspaces/users/<userId>/datasets<datasetId> where the userId is extracted from the tarball
# name and the dataset id is the data id given by irods to this particular file.  Once done, an event
# is created in json format which expands upon the dataset.json data by including the event (i.e., 'install')
# and the dataset id.
acLandingZonePostProcForPut(*fileDir, *fileName) {

    *literals = getLiterals();

	# insure the the user id is a positive number
	writeLine("serverLog", "Checking user id");
	*userId = int(trimr(triml(*fileName,"_u"),"_t"));  #expect file name in format dataset_u\d+_t\d+.tgz
	if(*userId <= 0) {
	    acSystemFailure(trimr(*fileName,"."), "IRODS acPostProcForPut Error", "The tarball filename, *fileName was mis-formatted.  No event was posted.");
	}

    # check user's workspace consumption and proceed only if under quota.
    writeLine("serverLog", "Checking whether user is already over quota.");
    acGetDefaultQuota(*defaultQuota);
	acGetWorkspaceUsed(*userId, *collectionSize);
	*quotaMegabytes = *defaultQuota/1000000;
	*message = "The dataset you are trying to export to EuPathDB would put you over your quota there.  Your quota there is *quotaMegabytes megabytes.";
	if(*collectionSize > *defaultQuota) {
	    acUserIssue(trimr(*fileName,"."), *message);
	    msiGoodFailure;
	}

	# check size of user's tarball so it if, even unpacked, it will put the user's workspace over quota
	writeLine("serverLog", "Checking whether user tarball will put user over quota.")
	*tarballFile = *fileDir ++ "/" ++ *fileName;
	acGetDataObjectSize(*tarballFile, *tarballSize);
	if(*tarballSize + *collectionSize > *defaultQuota) {
	    acUserIssue(trimr(*fileName,"."), *message);
	    msiGoodFailure;
	}

    # Any incidents here are system related issues.  They may be merely warnings (the user isn't notified) or they
    # may rise to the level of errors (the user receives an error message)

    # Both the warning and error messages are initialized to empty strings in preparation.
    *warning = "";
    *error = "";
    {
	    # Unpack the tarball into staging area.  The tarball $dataId will identify the dataset collection.
	    # Done first to staging to verify integrity of tarball since removing a bad dataset collection from
	    # the user's collection of datasets will trigger a PEP.  This approach avoids that.
	    *stagingDatasetPath = *literals.stagingAreaPath ++ "/$dataId";
        *userDatasetPath = "/ebrc/workspaces/users/*userId/datasets/$dataId";
	    writeLine("serverLog", "Unpacking *tarballFile to *stagingDatasetPath");
  	    msiTarFileExtract(*tarballFile, *stagingDatasetPath, $rescName, *actionStatus) ::: {
  	        *error = setIncidentMessage(*error, "Unable to unpack the tarball into the staging area.");
  	        *exists = checkForCollectionExistence(*stagingDatasetPath);
  	        if(*exists) {
  	          writeLine("serverLog", "Undo misTarFileExtract - remove the collection from the staging area.");
  	          msiRmColl(*stagingDatasetPath, "forceFlag=", *actionStatus);  # clean up the staging area
  	        }
  	    }

  	    # re-check site of user's new unpacked dataset to see whether the size, when added to the
  	    # current workspace, will put the user over quota.
  	    writeLine("serverLog", "Checking whether new unpacked user dataset will put user over quota");
  	    *datasetSize = getCollectionSize(*stagingDatasetPath);
  	    if(*datasetSize + *collectionSize > *defaultQuota) {
  	      acUserIssue(trimr(*fileName,"."), *message);
  	      msiGoodFailure;
  	    }

        # Create a new install event content in json format (action and recipient id do not apply here)
	    writeLine("serverLog", "Generating the install event data");
	    acGenerateEventJson(*stagingDatasetPath, "install", $dataId, "", "", *eventContent) ::: {
	        *error = setIncidentMessage(*error, "Unable to generate json content for the event file.");
	    }

	    # Unpack the tarball into the user's datasets collection now that it appears valid.  Valid means essentially
	    # that the tarball is unpackable and contains a dataset.json file.
	    writeLine("serverLog", "Unpacking the tarball into the user's datasets collection");
	    msiTarFileExtract(*tarballFile, *userDatasetPath, $rescName, *actionStatus) ::: {
	        *error = setIncidentMessage(*error, "Unable to unpack the tarball into the user's datasets collection.\n
	        Any leftover may compromise the GUI.");
	    }

        # Post the new json formatted install event
        writeLine("serverLog", "Posting the new install event in json format.");
	    *event = *eventContent.event;
	    *eventFileName = *eventContent.event_file_name;
	    writeLine("serverLog", "Event content to be posted is *event");
	    acPostNewEvent(*event, *eventFileName) ::: {
	        *error = setIncidentMessage(*error, "Unable to post the install event.");
	    }

        # Make a RESTful call to Jenkins to process the contents of the events collection.
	    writeLine("serverLog", "Triggering delivery of events to Jenkins.");
	    acTriggerEvent() ::: {
	        *error = "warning";
	        *warning = setIncidentMessage(*warning, "Unable to trigger the Jenkins listener.\n
	        Jenkins may be offline or the listener job maybe disabled.\n
	        A later scheduled run should pick up the install event.");
	    }

	    # Remove the tarball only if everything succeeds
	    writeLine("serverLog", "Removing *tarballFile tarball.");
	    msiDataObjUnlink("objPath=*tarballFile++++replNum=0++++forceFlag=",*actionStatus) ::: {
	        *error = "warning";
	        *warning = setIncidentMessage(*warning, "Unable to remove the tarball.");
	    }
	} ::: {
	    acSystemIssue(trimr(*fileName,"."), "IRODS acPostProcForPut", *warning, *error);
	}

	# Delete the user dataset placed in the staging area as we are now done with it.
    msiRmColl(*stagingDatasetPath, "forceFlag=", *actionStatus)

	# Write out a success message
	*message = "tarball *fileName unpacked to *userDatasetPath and event posted\n";
	acCreateCompletionFlag(trimr(*fileName,"."), *message, "success")
}


# This action is called by the acPostProcForPut action or the acPostProcForDelete action whenever a user
# grants or revokes a share to an owned dataset.  The WDK web service handles the placement or removal of the
# share via Jargon.  This action is called in response to that and simply provides a json formatted event
# to Jenkins to insure that the Oracle database is made consistent with this change.  The event extends
# dataset.json with the event (i.e., 'share'), the action (i.e., 'grant' or 'revoke'), the dataset that
# is the subject of the share event and the user id of the recipient of the share event.
acExternalPostProcForPutOrDelete(*fileDir, *fileName, *action) {
    writeLine("serverLog", "acExternalPostProcForPutOrDelete for *action of *fileName from *fileDir");

    # Identify the user id of the recipient
    msiSplitPath(*fileDir, *recipientPath, *trash);
    msiSplitPath(*recipientPath, *trashPath, *recipientId);

    # The name of the file that was added/removed is expected to be in the form ownerId.externalDatasetId
	*ownerId = trimr(*fileName,".");
	*externalDatasetId = triml(*fileName,".");
	writeLine("serverLog", "Owner id is *ownerId, Recipient id is *recipientId and External Dataset id is *externalDatasetId");
	
    # Fabricate an external dataset event.
	*ownerDatasetPath = "/ebrc/workspaces/users/*ownerId/datasets/*externalDatasetId";

    # Create a new event content in json format
	writeLine("serverLog", "Generating the share (*action) event data");
	acGenerateEventJson(*ownerDatasetPath, "share", *externalDatasetId, *action, *recipientId, *eventContent);

    # Post the new json formatted share event
    writeLine("serverLog", "Posting the new share (*action) event in json format.");
    *event = *eventContent.event;
	*eventFileName = *eventContent.event_file_name;
	writeLine("serverLog", "Event content to be posted is *event");
	acPostNewEvent(*event, *eventFileName);

	acTriggerEvent();
}


# This action is called by the acPreprocForRmColl action just before a dataset is removed.  The
# WDK web service handles the removal the the subject dataset collection.  This action is called
# in response to that and simply provides a json formatted event to Jenkins to insure that the
# Oracle database is made consistent with this change.  The event extends dataset.json with the
# event (i.e., 'uninstall') and id of the dataset to be deleted.
acDatasetPreprocForRmColl() {
    writeLine("serverLog", "acDatasetPreprocForRmColl for $collName");

    # Extract the dataset id from the collection path provided.
	msiSplitPath($collName, *parent, *datasetId);

    # Both the warning and error messages are initialized to empty strings in preparation.
    *warning = "";
    *error = "";
    {
        # Create a new uninstall event content in json format
	    writeLine("serverLog", "Generating the uninstall event data");
	    acGenerateEventJson($collName, "uninstall", *datasetId, "", "", *eventContent) ::: {
	        *error = setIncidentMessage(*error, "Unable to generate the uninstall event content.");
	    }

	    # Post the new json formatted uninstall event
        writeLine("serverLog", "Posting the new uninstall event in json format.");
        *event = *eventContent.event;
	    *eventFileName = *eventContent.event_file_name;
	    writeLine("serverLog", "Event content to be posted is *event");
	    acPostNewEvent(*event, *eventFileName) ::: {
	        *error = setIncidentMessage(*error, "Unable to post the uninstall event.");
	    }

	    # Make a RESTful call to Jenkins to process the contents of the events collection.
	    writeLine("serverLog", "Triggering delivery of events to Jenkins.");
	    acTriggerEvent() ::: {
	        *error = "warning";
	        *warning = setIncidentMessage(*warning, "Unable to trigger the Jenkins listener.\n
	        Jenkins may be offline or the listener job maybe disabled.\n
	        A later scheduled run should pick up the install event.");
	    }
	} ::: {
	    acSystemIssue(trimr(*datasetId, "."), "IRODS acPreprocForRmColl", *warning, *error);
	}
}

# ------------------------- Utilities --------------------- #

# This action posts the event json object to a json file in the events
# collection.  The (hopefully) unique file name is provided.
acPostNewEvent(*event, *eventFileName) {
  *literals = getLiterals();
  *eventPath = *literals.eventsPath ++ "/*eventFileName";
  msiDataObjCreate(*eventPath,"null",*eventFileDescriptor);
  msiDataObjWrite(*eventFileDescriptor,*event,*fileLength);
  msiDataObjClose(*eventFileDescriptor,*eventStatus);
  writeLine("serverLog", "Created event file *eventFileName");
}

# Returns the integer size, in bytes, of the datasets currently in the user's workspace.
acGetWorkspaceUsed(*userId, *collectionSize) {
    *literals = getLiterals();
    *collection = *literals.usersPath ++ "/*userId";
    *collectionSize = getCollectionSize(*collection);
    writeLine("serverLog", "Workspace collection size for *collection is *collectionSize bytes");
}


# Returns the integer default quota size in bytes.  The assumption is this file contains only a number (digits only)
# in bytes, followed by a newline.
acGetDefaultQuota(*defaultQuota) {
    *literals = getLiterals();
    *quotaFile = *literals.defaultQuotaPath;
    acGetDataObjectSize(*quotaFile, *quotaFileSize)
    msiDataObjOpen("objPath=*quotaFile++++replNum=0++++openFlags=O_RDONLY", *quotaFileDescriptor);
	msiDataObjRead(*quotaFileDescriptor, *quotaFileSize, *quotaData);
	msiStrchop(str(*quotaData), *defaultQuota);
	msiDataObjClose(*quotaFileDescriptor, *quotaFileStatus);
	*defaultQuota = int(*defaultQuota);
}

# This action takes the dataset.json file found in the path given by the first argument and uses that as a
# template for creating event content.  That json data along with the event, the dataset id, and any
# action or recipient information is sent to a python script that re-composes the json object with the
# additional information.  The result returned is a key/value pair set where the keys include the event
# itelf (in json format) and the name of the event file (where the timestamp used to hopefully make
# the event file unique is provided by that python script).
acGenerateEventJson(*userDatasetPath, *event, *datasetId, *action, *recipient, *eventContent) {
    writeLine("serverLog", "acGenerateEventJson for *userDatasetPath, *event, *datasetId, *action, *recipient");
    *datasetConfigFile = "*userDatasetPath/dataset.json";
	acGetDataObjectSize(*datasetConfigFile, *datasetConfigFileSize);
	msiDataObjOpen("objPath=*datasetConfigFile++++replNum=0++++openFlags=O_RDONLY", *datasetConfigFileDescriptor);
	msiDataObjRead(*datasetConfigFileDescriptor, *datasetConfigFileSize, *datasetConfigData);
	# Escapes the double quotes so that the content is transmitted as an intact single string.
	*datasetConfigDataStr = execCmdArg(str(*datasetConfigData));
	msiDataObjClose(*datasetConfigFileDescriptor, *datasetConfigFileStatus);
	*eventStr = execCmdArg(str(*event));
	*datasetIdStr = execCmdArg(str(*datasetId));
	*actionStr = execCmdArg(str(*action));
	*recipientStr = execCmdArg(str(*recipient));
	*argStr = '*datasetConfigDataStr  *eventStr *datasetIdStr *actionStr *recipientStr';
	msiExecCmd("eventGenerator.py",*argStr,"null","null","null",*eventOutput);
	msiGetStdoutInExecCmdOut(*eventOutput, *eventOut);
	msiString2KeyValPair(*eventOut, *eventContent);
}

# Fires off the RESTful call to Jenkins to process the event file.  The jobFile variable provides the data needed to call
# Jenkins.
acTriggerEvent() {
    *literals = getLiterals();
	*jobFile = *literals.jobFilePath;
	acGetDataObjectSize(*jobFile, *jobFileSize);
	msiDataObjOpen("objPath=*jobFile++++replNum=0++++openFlags=O_RDONLY", *jobFileDescriptor);
	msiDataObjRead(*jobFileDescriptor, *jobFileSize, *jobData);
    *argv = str(*jobData);
	writeLine("serverLog", "Passing *argv");
    msiExecCmd("executeJobFile.py", *argv, "null", "null", "null", *jobResult);
    msiGetStdoutInExecCmdOut(*jobResult, *out);
	writeLine("serverLog", "Output from the python call: *out");
}

# Provides a status flag, with the outcome as part of the flag file name, that provides some insight into the
# the successful and failed attempts at manipulating iRODS file data.
acCreateCompletionFlag(*identifier, *message, *outcome) {
    *statusFileName = *outcome ++ "_" ++ *identifier;
    writeLine("serverLog", "Creating status flag for *statusFileName");
    *statusFile = "/ebrc/workspaces/flags/*statusFileName";
    msiDataObjCreate(*statusFile,"forceFlag=",*statusFileDescriptor);
    msiDataObjWrite(*statusFileDescriptor, *message, *statusFileSize);
    msiDataObjClose(*statusFileDescriptor, *statusFileStatus);
}

# Convenience method for getting the integer size in bytes of a data object
acGetDataObjectSize(*dataObject, *dataObjectSize) {
    msiSplitPath(*dataObject, *dataObjectPath, *dataObjectName);
    *results = SELECT DATA_SIZE WHERE COLL_NAME = *dataObjectPath AND DATA_NAME = *dataObjectName;
    *dataObjectSize = 0;
	foreach(*results) {
	  *dataObjectSize = int(*results.DATA_SIZE);
	}
}

# Related to user issues.  User gets an informative message only and the action terminates.
acUserIssue(*identifier, *message) {
    acCreateCompletionFlag(*identifier, *message, "failure");
    msiGoodFailure;
}

# Relates to system issues outside of the user's control.  In the case of an error, a generic failure status file is
# available and an email is posted to the EuPath mailing list with more detail.  In the case of a warning, a success
# status file is available but an email containing the warning is sent to the EuPath mailing list.
acSystemIssue(*identifier, *subject, *warning, *error) {
    if(*error != 'warning') {
        writeLine("serverLog", "Error *subject - *identifier : *error");
        *userMessage = "The export did not proceed properly.  EuPathDB staff are looking into the issue.";
        msiSendMail("criswlawrence@gmail.com", "Error *subject", "*identifier: *error");
        acCreateCompletionFlag(*identifier, *userMessage, "failure");
    }
    else {
        writeLine("serverLog","Warning *subject - *identifier : *warning");
        msiSendMail("criswlawrence@gmail.com", "Warning *subject", "*identifier: *warning");
        acCreateCompletionFlag(*identifier, *warning, "success");
    }
    msiGoodFailure;
}

# Set the incident message only if not already set - strategy courtesy of Mark Heiges
setIncidentMessage(*prior, *new) = {
    if (strlen(*prior) == 0) {
        *new;
    }
    else {
        *prior;
    }
}

# Convenience method to check for the existence of a data object (file).
checkForDataObjectExistence(*dataObjectPath, *dataObjectName) = {
    *results = SELECT COUNT(DATA_ID) WHERE COLL_NAME = '*dataObjectPath' AND DATA_NAME = '*dataObjectName';
	*count = 0;
	foreach(*result in *results) {
	  *count = int(*result.DATA_ID);
	}
	*count > 0;
}

# Convenience method to check for the existence of a collection (folder).
checkForCollectionExistence(*collection) = {
    *results = SELECT COUNT(COLL_NAME) WHERE COLL_NAME = '*collection';
	*count = 0;
	foreach(*result in *results) {
	  *count = int(*result.COLL_NAME);
	}
    *count > 0;
}

# A collection of literals for paths through the workspace done in an effort
# to keep these literals in one place.
getLiterals() = {
  *literals.homePath = "/ebrc/workspaces";
  *literals.stagingAreaPath = *literals.homePath ++ "/staging";
  *literals.flagsPath = *literals.homePath ++ "/flags";
  *literals.usersPath = *literals.homePath ++ "/users";
  *literals.eventsPath = *literals.homePath ++ "/events";
  *literals.defaultQuotaPath = *literals.usersPath ++ "/default_quota";
  *literals.landingZonePath = *literals.homePath ++ "/lz";
  *literals.jobFilePath = *literals.homePath ++ "/jenkinsCommunicationConfig.txt";
  #writeLine("serverLog","Literals: *literals");
  *literals;
}

# Convenience method to retrieve the size, in bytes, occupied by a collection.
getCollectionSize(*collection) = {
  *results =  SELECT SUM(DATA_SIZE) WHERE COLL_NAME LIKE '*collection/%';
  *collectionSize = 0;
  # One iteration only expected
  foreach(*result in *results) {
    *collectionSize = int(*result.DATA_SIZE);
  }
  *collectionSize;
}