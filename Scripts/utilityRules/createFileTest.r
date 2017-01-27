utilCreateAFile {
  writeLine("stdout", "Starting creation of a file");
  msiDataObjCreate(*dataObj,"forceFlag=",*fileDescriptor);
  msiDataObjWrite(*fileDescriptor,"I am in!",*fileSize);
  msiDataObjClose(*fileDescriptor,*status);
  writeLine("stdout", "File creation complete");
}
input  *dataObj = "/ebrc/workspaces/flags/success-test"
output ruleExecOut
