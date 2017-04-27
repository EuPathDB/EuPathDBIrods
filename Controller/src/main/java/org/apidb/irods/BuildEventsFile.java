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
import org.gusdb.wdk.model.user.dataset.UserDatasetSession;
import org.gusdb.wdk.model.user.dataset.UserDatasetStore;
import org.gusdb.wdk.model.user.dataset.UserDatasetStoreAdaptor;
import org.gusdb.wdk.model.user.dataset.event.UserDatasetEventArrayHandler;
import org.json.JSONArray;
import org.json.JSONObject;
import org.xml.sax.SAXException;

/**
 * This is a small Java application that should be called by Jenkins whenever an IRODS event of note takes
 * place and also periodically, given the possibility that a prior event was not captured.  It reads the
 * contents of each file in the entire IRODS events folder, and consolidates them into a single JSON array of events
 * that is passed on to the WDK's user dataset events handler for processing according to the nature of each
 * event. Although this project is specifically meant to address event handling intended for IRODS, it has no specific references
 * to IRODS.  It could be used with a POSIX system as well.
 * 
 * @author crisl-adm
 */
public class BuildEventsFile {

  private static final Logger logger = Logger.getLogger(BuildEventsFile.class);	
  public static final String EVENTS_DIR = "/ebrc/workspaces/events";

  public static void main(String[] args) throws Exception {
	  
	// The id of the project for which these events are intended.
    String projectId = System.getenv("PROJECT_ID");
    
    // Identifies the datastore associated with the events to be handled.  Used to insure that this datastore
    // matches the one this build supports.
    String datasetStoreId = System.getenv("DATASET_STORE_ID");
 
    logger.info("Parameters - Project: " + projectId + ", Dataset Store: " + datasetStoreId);
    
    // A model configuration file must exist for every project this program may possibly support.
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
    
    // Insures that the appropriate datastore is calling this method.
    ModelConfigUserDatasetStore dsConfig = modelConfig.getUserDatasetStoreConfig();
    UserDatasetStore dsStore = dsConfig.getUserDatasetStore();
    JSONArray eventJsonArray = new JSONArray();
    try(UserDatasetSession dsSession = dsStore.getSession(dsStore.getUsersRootDir())) {		
      if(!dsSession.getUserDatasetStoreId().equals(datasetStoreId)) {
        throw new RuntimeException("Called by wrong datastore " + datasetStoreId);
      }
    
      // Collect all the event files from the events folder in the datastore.
      UserDatasetStoreAdaptor dsAdaptor = dsSession.getUserDatasetStoreAdaptor();
      List<Path> eventFiles = new ArrayList<>();
      try {
        eventFiles = dsAdaptor.getPathsInDir(Paths.get(EVENTS_DIR));
      }
      catch (WdkModelException e) {
        e.printStackTrace();
        throw new RuntimeException(e);
      }
    
      // Read the contents of those json formatted event files into JSON objects and collect
      // those JSON objects into a JSON array.
      for(Path eventFile : eventFiles) {
        if(eventFile.getFileName().toString().endsWith(".json")) {
          String event = dsAdaptor.readFileContents(eventFile);
          JSONObject eventJson = new JSONObject(event);
          eventJsonArray.put(eventJson);
        }
      }
      logger.info("Events JSON array:" + eventJsonArray.toString());
    }
    // Create a dataset event handler to further process the resulting events JSON array.
    UserDatasetEventArrayHandler handler = new UserDatasetEventArrayHandler();
    handler.setProjectId(projectId);
    Path tmpDir =  Paths.get(handler.getWdkTempDirName());
    handler.handleEventList(UserDatasetEventArrayHandler.parseEventsArray(eventJsonArray),
                            modelConfig.getUserDatasetStoreConfig().getTypeHandlers(), tmpDir);
  }

}
