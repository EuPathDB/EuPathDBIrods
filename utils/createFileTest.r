utilCreateAFile {
  writeLine("stdout", "Starting creation of a file");
  msiDataObjCreate(*dataObj,"forceFlag=",*fileDescriptor);
  msiDataObjClose(*fileDescriptor,*status);
  writeLine("stdout", "File creation complete");
}
input  *dataObj = "/ebrc/workspaces/A"
output ruleExecOut
