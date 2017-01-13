# Removes ALL user datasets (users remain intact)
utilDeleteAllDatasets {

         *flushFile = "/ebrc/workspaces/flushMode";
         msiDataObjCreate(*flushFile,"null",*flushFileDescriptor);
         msiDataObjClose(*flushFileDescriptor,*fileStatus);
         writeLine("stdout", "Starting deletion of all user datasets");
		 *Datasets = SELECT COLL_NAME WHERE COLL_PARENT_NAME like *Location;
         foreach(*Datasets) {
           msiRmColl(*Datasets.COLL_NAME, *Flag, *Status);
           writeLine("stdout", "Removed" ++ *Datasets.COLL_NAME);
         }
         msiDataObjUnlink("objPath=*flushFile++++replNum=0++++forceFlag=",*DelStatus);
 }
input  *Location = "/ebrc/workspaces/users/%/datasets", *Flag="forceFlag="
output ruleExecOut
