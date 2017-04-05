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
import org.gusdb.wdk.model.user.dataset.event.UserDatasetEventArrayHandler;
import org.gusdb.wdk.model.user.dataset.event.UserDatasetEventListHandler;
import org.json.JSONArray;
import org.json.JSONObject;
import org.xml.sax.SAXException;

/**
 * This is a small Java application that should be called by Jenkins whenever an IRODS event of note takes
 * place and also periodically, given the possibility that a prior event was not captured.  It reads the
 * contents of each file in the entire IRODS events folder, and consolidates them into a single list of events
 * that is passed on to the WDK's user dataset events handler to processing according to the nature of each
 * event. Although this file addresses event handling is intended for IRODS, it has no specific references
 * to IRODS.  It could be used with a POSIX system as well.
 * 
 * @author crisl-adm
 */
public class BuildEventsFile {

  private static final Logger logger = Logger.getLogger(BuildEventsFile.class);	
  public static final String EVENTS_DIR = "/ebrc/workspaces/events";

  public static void main(String[] args) throws Exception {
    String projectId = System.getenv("PROJECT_ID");
    String datasetStoreId = System.getenv("DATASET_STORE_ID");
    logger.info("Parameters - Project: " + projectId + ", Dataset Store: " + datasetStoreId);
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
    // Insures that only the correct IRODS is calling this method.
    if(!uds.getUserDatasetStoreId().equals(datasetStoreId)) {
      throw new RuntimeException("Called by wrong IRODS " + datasetStoreId);
    }
    UserDatasetStoreAdaptor udsa = uds.getUserDatasetStoreAdaptor();
    List<Path> eventFiles = new ArrayList<>();
    try {
      eventFiles = udsa.getPathsInDir(Paths.get(EVENTS_DIR));
    }
    catch (WdkModelException e) {
      e.printStackTrace();
      throw new RuntimeException(e);
    }
    JSONArray eventJsonArray = new JSONArray();
    for(Path eventFile : eventFiles) {
      if(eventFile.getFileName().toString().endsWith(".json")) {	
        String event = udsa.readFileContents(eventFile);
        JSONObject eventJson = new JSONObject(event);
        eventJsonArray.put(eventJson);
      }  
    }
    System.out.println(eventJsonArray.toString());
    UserDatasetEventArrayHandler handler = new UserDatasetEventArrayHandler();
    handler.setProjectId(projectId);
    Path tmpDir =  Paths.get(handler.getWdkTempDirName());
    handler.handleEventList(UserDatasetEventArrayHandler.parseEventsArray(eventJsonArray),
        modelConfig.getUserDatasetStoreConfig().getTypeHandlers(), tmpDir);
  }

}
