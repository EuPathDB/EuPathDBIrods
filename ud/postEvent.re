# This rule posts the content provided to a new event data object in the events
# collection.  The use of systemTime in the event data object name may not be sufficient
# to insure uniqueness.  May need to obtain something from the caller to help insure that.
acPostEvent(*eventContent) {
  msiGetIcatTime(*systemTime,"unix");
  *fileName = "event_*systemTime.txt";
  *eventPath = "/ebrc/workspaces/events/*fileName";
  msiDataObjCreate(*eventPath,"destRescName=$rescName",*eventFileDescriptor);
  msiDataObjWrite(*eventFileDescriptor,*eventContent,*fileLength);
  msiDataObjClose(*eventFileDescriptor,*eventStatus);
  writeLine("serverLog", "Created event file *fileName");
}	