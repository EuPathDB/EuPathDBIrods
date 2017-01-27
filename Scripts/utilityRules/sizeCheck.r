checkUserWorkspaceUsed {
  *results =  SELECT SUM(DATA_SIZE) WHERE COLL_NAME LIKE '/ebrc/workspaces/users/*userId/datasets/%';
  *collectionSize = 0;
	foreach(*result in *results) {
	  *collectionSize = *result.DATA_SIZE;
	}
}
input  *userId = '108976930'
output *collectionSize, ruleExecOut