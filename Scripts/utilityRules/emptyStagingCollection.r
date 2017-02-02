# Removes ANY residual datasets in the staging collection
utilEmptyStagingCollection {
    writeLine("stdout", "Starting deletion of all staging datasets");
    *datasets = SELECT COLL_NAME WHERE COLL_PARENT_NAME like *targetCollection;
    foreach(*datasets) {
        msiRmColl(*datasets.COLL_NAME, *flag, *status);
        writeLine("stdout", "Removed from staging " ++ *datasets.COLL_NAME);
    }
}
input  *targetCollection = "/ebrc/workspaces/staging", *flag="forceFlag="
output ruleExecOut
