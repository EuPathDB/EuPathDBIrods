# Called once a dataset tarball is unpacked and placed in the owner's collection.  Reads the
# accompanying dataset.json data object, calls a python script the parse the json into a more
# digestable format and returns the data according to the following tab delimited format:
# content: 'install' projects user_dataset_id ud_type_name ud_type_version owner_user_id dependency dependency_version
acCreateEventContentForUnpack(*userDatasetPath, *userId, *datasetId, *content) {
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
	*content = "install\tnull\t*datasetId\t" ++ *pairs.ud_type_name ++ "\t" ++ *pairs.ud_type_version ++ "\t*userId\t" ++ *pairs.dependency ++ "\t" ++ *pairs.dependency_version ++ "\n";
	writeLine("serverLog", *content);
}