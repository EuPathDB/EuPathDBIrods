# Flushes ALL files in the flags collection
utilEmptyFlagsCollection {
  writeLine("stdout", "Starting deletion of all flags content");
  *results = SELECT DATA_NAME WHERE COLL_NAME == *targetCollection;
  foreach(*results) {
    *targetDataObject = *results.DATA_NAME;
    *targetDataObjectPath = "*targetCollection/*targetDataObject";
    msiDataObjUnlink("objPath=*targetDataObjectPath",*Status);
	writeLine("stdout", "Removed *targetDataObject");
  }
}
input  *targetCollection = "/ebrc/workspaces/flags"
output ruleExecOut