acPostEvent(*eventContent) {
  msiGetIcatTime(*systemTime,"unix");
  *fileName = "event_*systemTime.txt";
  *eventPath = "/ebrc/workspaces/events/*fileName";
  msiDataObjCreate(*eventPath,"destRescName=$rescName++++forceFlag=",*eventFileDescriptor);
  msiDataObjWrite(*eventFileDescriptor,*eventContent,*fileLength);
  msiDataObjClose(*eventFileDescriptor,*eventStatus);
  writeLine("serverLog", "Created event file *fileName");
}	