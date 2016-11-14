utilDeleteAllDatasets {
         writeLine("stdout", "Starting deletion of all user datasets");
		 *Datasets = SELECT COLL_NAME WHERE COLL_NAME like *Location;
         foreach(*Datasets) {
		   if(*Datasets.COLL_NAME not like "/ebrc/workspaces/users/*/datasets/*/*") {
             msiRmColl(*Datasets.COLL_NAME, *Flag, *Status);
             writeLine("stdout", "Removed" ++ *Datasets.COLL_NAME);
		   }	 
         }
 }
input  *Location = "/ebrc/workspaces/users/%/datasets/%", *Flag="forceFlag="
output ruleExecOut
