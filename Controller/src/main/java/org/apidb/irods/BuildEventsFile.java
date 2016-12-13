package org.apidb.irods;

import java.io.IOException;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import org.apache.log4j.Logger;
import org.gusdb.wdk.model.Utilities;
import org.gusdb.wdk.model.WdkModelException;
import org.gusdb.wdk.model.config.ModelConfig;
import org.gusdb.wdk.model.config.ModelConfigParser;
import org.gusdb.wdk.model.config.ModelConfigUserDatasetStore;
import org.gusdb.wdk.model.user.dataset.UserDatasetStore;
import org.gusdb.wdk.model.user.dataset.UserDatasetStoreAdaptor;
import org.gusdb.wdk.model.user.dataset.event.UserDatasetEventListHandler;
import org.xml.sax.SAXException;



public class BuildEventsFile {

  private static final Logger logger = Logger.getLogger(BuildEventsFile.class);	
  public static final String EVENTS_DIR = "/ebrc/workspaces/events";
	
  public static void main(String[] args) throws Exception {
	String projectId = System.getenv("PROJECT_ID");
	logger.debug("Project: " + projectId);
	System.out.println("Project: " + projectId);
	String gusHome = System.getProperty(Utilities.SYSTEM_PROPERTY_GUS_HOME);     
    ModelConfigParser parser = new ModelConfigParser(gusHome);
    ModelConfig modelConfig = null;
	try {
	  modelConfig = parser.parseConfig(projectId);
	} 
	catch(WdkModelException | SAXException | IOException e) {
	  e.printStackTrace();
	  throw new RuntimeException(e);
	}
	ModelConfigUserDatasetStore udsConfig = modelConfig.getUserDatasetStoreConfig();
    UserDatasetStore uds = udsConfig.getUserDatasetStore();
	UserDatasetStoreAdaptor udsa = uds.getUserDatasetStoreAdaptor();
	List<Path> eventFiles = new ArrayList<>();
	try {
	  eventFiles = udsa.getPathsInDir(Paths.get(EVENTS_DIR));
	}
	catch (WdkModelException e) {
	  e.printStackTrace();
	  throw new RuntimeException(e);
	}
	StringBuilder events = new StringBuilder();
	List<String> eventList = new ArrayList<>();
	for(Path eventFile : eventFiles) {
	  String eventFilename = eventFile.getFileName().toString();
	  String timestamp = eventFilename.substring(eventFilename.indexOf('_') + 1, eventFilename.indexOf('.'));
	  String event = udsa.readFileContents(eventFile);
	  events.append(timestamp + "\t" + event + System.getProperty("line.separator"));
	  eventList.add(timestamp + "\t" + event);
	} 
	System.out.println(events.toString());
	String cmdName = System.getProperty("cmdName");
	UserDatasetEventListHandler handler = new UserDatasetEventListHandler(cmdName);
	handler.parseEventsList(eventList);
	logger.debug("Handler call complete");
  }

}
