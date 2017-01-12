# Flushes all event files from the events collection
utilEmptyEventsCollection {
  writeLine("stdout", "Starting deletion of all events");
  *results = SELECT DATA_NAME WHERE COLL_NAME == *eventCollection;
  foreach(*results) {
    *eventDataObject = *results.DATA_NAME;
    *eventDataObjectPath = "*eventCollection/*eventDataObject";
    msiDataObjUnlink("objPath=*eventDataObjectPath",*Status);
	writeLine("stdout", "Removed *eventDataObject");
  }
}
input  *eventCollection = "/ebrc/workspaces/events"
output ruleExecOut