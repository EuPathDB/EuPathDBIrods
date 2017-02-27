# Removes ALL external datasets (users remain intact)
utilDeleteAllExternalDatasets {

  writeLine("stdout", "Starting deletion of all external datasets");
  *ExternalDatasetUsers = SELECT COLL_PARENT_NAME WHERE COLL_NAME like *Location;
  foreach(*ExternalDatasetUsers) {
    *externalDatasetsPath = *ExternalDatasetUsers.COLL_PARENT_NAME ++ "/externalDatasets";
    msiRmColl(*externalDatasetsPath, *Flag, *Status);
    writeLine("stdout", "Removed External Datasets for User " ++ *ExternalDatasetUsers.COLL_PARENT_NAME);
  }
 }
input  *Location = "/ebrc/workspaces/users/%/externalDatasets", *Flag="forceFlag="
output ruleExecOut