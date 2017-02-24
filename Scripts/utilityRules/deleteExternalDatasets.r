# Removes ALL external datasets (users remain intact)
utilDeleteAllExternalDatasets {

  writeLine("stdout", "Starting deletion of all external datasets");
  *ExternalDatasets = SELECT COLL_NAME WHERE COLL_PARENT_NAME like *Location;
  foreach(*ExternalDatasets) {
    msiRmColl(*ExternalDatasets.COLL_NAME, *Flag, *Status);
    writeLine("stdout", "Removed External Datasets for User " ++ *ExternalDatasets.COLL_PARENT_NAME);
  }
 }
input  *Location = "/ebrc/workspaces/users/%/externalDatasets", *Flag="forceFlag="
output ruleExecOut