package org.apidb.irods;

import java.nio.file.Path;
import java.util.LinkedList;

import javax.sql.DataSource;

import org.apache.log4j.Logger;
import org.gusdb.fgputil.db.pool.DatabaseInstance;
import org.gusdb.fgputil.json.JsonUtil;
import org.gusdb.wdk.model.WdkModel;
import org.gusdb.wdk.model.WdkModelException;
import org.gusdb.wdk.model.user.dataset.UserDatasetSession;
import org.gusdb.wdk.model.user.dataset.UserDatasetStoreAdaptor;
import org.gusdb.wdk.model.user.dataset.event.UserDatasetEventCleanup;
import org.gusdb.wdk.model.user.dataset.event.UserDatasetEventSync;
import org.gusdb.wdk.model.user.dataset.event.raw.EventParser;
import org.gusdb.wdk.model.user.dataset.event.raw.UDEvent;

/**
 * This is a small Java application that should be called by Jenkins whenever an
 * iRODS event of note takes place and also periodically, given the possibility
 * that a prior event was not captured.  It reads the contents of each file in
 * the entire iRODS events folder, and consolidates them into a single JSON
 * array of events that is passed on to the WDK's user dataset events handler
 * for processing according to the nature of each event.
 *
 * Although this project is specifically meant to address event handling
 * intended for iRODS, it has no specific references to iRODS.  It could be used
 * with a POSIX system as well.
 *
 * @author crisl-adm
 */
public class ProcessIrodsEvents {

  private static final Logger logger = Logger.getLogger(ProcessIrodsEvents.class);
  public static final String EVENTS_DIR = "/ebrc/workspaces/events";

  public static void main(String[] args) throws Exception {

	// The id of the project for which these events are intended.
    String projectId = System.getenv("PROJECT_ID");

    // Identifies the datastore associated with the events to be handled.
    // Used to insure that this datastore matches the one this build supports.
    String datasetStoreId = System.getenv("DATASET_STORE_ID");

    String mode = System.getenv("RUN_MODE");

    logger.info("Parameters - Project: " + projectId
      + ", Dataset Store: " + datasetStoreId
      + ", Run Mode: " + mode);

    switch (mode) {
      case "sync":
        syncMode(projectId, datasetStoreId);
        break;
      case "cleanup":
        cleanupMode(projectId);
        break;
      default:
        logger.error("Unset or invalid RUN_MODE value.  Must be one of \"sync\" or \"cleanup\".");
    }
  }

  private static void syncMode(String projectId, String datasetStoreId) throws WdkModelException {
    var eventJsonArray = new LinkedList<UDEvent>();

    // Create a dataset event handler to process the resulting events list.
    // The dataset event handler constructor uses the provided projectId
    // to initialize and populate the user dataset store and provide the
    // temporary directory url.
    var handler = new UserDatasetEventSync(projectId);
    var dsStore = handler.getUserDatasetStore();

    // Open the user dataset session for processing the event list.
    try(UserDatasetSession dsSession = dsStore.getSession(dsStore.getUsersRootDir())) {

      // Insure that the dataset store that triggered this event handling
      // operation is the same as the one with which this code communicates.
      if(dsStore.getId() == null || !dsStore.getId().equals(datasetStoreId)) {
        throw new RuntimeException("Called by wrong datastore " + datasetStoreId + ". Expecting " + dsStore.getId());
      }

      // Collect a subset of the event files from the events folder in the
      // datastore.
      UserDatasetStoreAdaptor dsAdaptor = dsSession.getUserDatasetStoreAdaptor();
      Long lastHandledEventId = null;
      try (DatabaseInstance appDb = new DatabaseInstance(handler.getModelConfig().getAppDB(), WdkModel.DB_INSTANCE_APP, true)) {
          DataSource appDbDataSource = appDb.getDataSource();
          lastHandledEventId = handler.findLastHandledEvent(appDbDataSource);
      }
      catch (Exception e) {
        throw new WdkModelException(e);
      }

      logger.info("Last handled event: " + lastHandledEventId);

      // Read the contents of recent json formatted event files into JSON
      // objects and collect those JSON objects into a JSON array.
      //TODO - eventJsonArray could produce big memory footprint if we handle large number of event files.
      for(Path eventFile : dsSession.getRecentEvents(EVENTS_DIR, lastHandledEventId == null ? 0L : lastHandledEventId)) {
        if(eventFile.getFileName().toString().endsWith(".json")) {
          String event = dsAdaptor.readFileContents(eventFile);
          var eventJson = EventParser.parseSingle(event);
          eventJsonArray.add(eventJson);
        }
      }
      logger.info("Events JSON array:" + JsonUtil.prettyPrint(eventJsonArray));

      // Process the events
      handler.handleEventList(UserDatasetEventSync.parseEventsArray(eventJsonArray));
    }
  }

  private static void cleanupMode(String projectID) throws WdkModelException {
    new UserDatasetEventCleanup(projectID).cleanupFailedInstalls();
  }
}
