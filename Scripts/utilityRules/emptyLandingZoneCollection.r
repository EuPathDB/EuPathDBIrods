# Flushes ALL files in the landing zone collection
utilEmptyLandingZoneCollection {
  writeLine("stdout", "Starting deletion of all landing zone content");
  *results = SELECT DATA_NAME WHERE COLL_NAME == *landingZoneCollection;
  foreach(*results) {
    *landingZoneDataObject = *results.DATA_NAME;
    *landingZoneDataObjectPath = "*landingZoneCollection/*landingZoneDataObject";
    msiDataObjUnlink("objPath=*landingZoneDataObjectPath",*Status);
	writeLine("stdout", "Removed *landingZoneDataObject");
  }
}
input  *landingZoneCollection = "/ebrc/workspaces/lz"
output ruleExecOut