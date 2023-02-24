package org.apidb.irods;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

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
 * <h2>Runtime Configuration</h2>
 *
 * This script requires the following configuration to be set on the environment
 * to execute:
 *
 * <dl>
 *   <dt><code>PROJECT_ID</code></dt>
 *   <dd><b>REQUIRED</b> Target project that events should be processed for.
 *       Events that are for other projects will be skipped.</dd>
 *   <dt><code>DATASET_STORE_ID</code></dt>
 *   <dd><b>REQUIRED</b> Identifies the datastore associated with the events to
 *       be handled.  This value is used to ensure that this datastore matches
 *       the one the current build supports.</dd>
 *   <dt><code>RUN_MODE</code></dt>
 *   <dd><b>REQUIRED</b> Selects the operation mode the script will execute in.
 *       Must be one of &quot;<code>sync</code>&quot; or
 *       &quot;<code>cleanup</code>&quot;.  <code>sync</code> mode synchronizes
 *       the datasets from iRODS into the database.  <code>cleanup</code> mode
 *       performs cleanup steps to resolve issues encountered when last syncing
 *       datasets.</dd>
 *   <dt><code>MAX_EVENTS</code></dt>
 *   <dd><b>OPTIONAL</b> Sets the maximum number of events to process in a
 *       single execution of the script.  This value paginates the events coming
 *       from iRODS to avoid issues with connection leaks that are encountered
 *       on long running Jargon-iRODS sessions.<br><br>Defaults to 150</dd>
 * </dl>
 *
 * @author crisl-adm
 */
public class ProcessIrodsEvents {

  // region Environment configuration variables

  private static final String ENV_PROJECT_ID = "PROJECT_ID";

  private static final String ENV_PROJECT_IDS = "PROJECT_IDS";

  private static final String ENV_DATASTORE_ID = "DATASET_STORE_ID";

  private static final String ENV_RUN_MODE = "RUN_MODE";

  private static final String ENV_MAX_EVENTS = "MAX_EVENTS";

  // endregion Environment configuration variables


  private static final Logger logger = Logger.getLogger(ProcessIrodsEvents.class);

  /**
   * Default maximum number of events to handle per script execution.
   *
   * This value may be overridden using the environment variable
   * {@code MAX_EVENTS}.
   */
  private static final int DEFAULT_MAX_EVENTS_PER_EXEC = 150;

  public static final String EVENTS_DIR = "/ebrc/workspaces/events";

  public static void main(String[] args) throws Exception {

    String rawProjectIds = System.getenv(ENV_PROJECT_IDS);
    String projectId = System.getenv(ENV_PROJECT_ID);
    List<String> projectIds;
    if (rawProjectIds == null && projectId == null) {
      throw new IllegalStateException("Only one of " + ENV_PROJECT_ID + " or " + ENV_PROJECT_IDS + " must be set in environment");
    }

    if (rawProjectIds != null && projectId != null) {
      throw new IllegalStateException("Exactly one of " + ENV_PROJECT_ID + " and " + ENV_PROJECT_IDS + " must be set in environment");
    }

    // The id of the project for which these events are intended.
    if (rawProjectIds != null) {
      projectIds = Arrays.asList(rawProjectIds.split(","));
    } else {
      projectIds = Arrays.asList(projectId);
    }

    // Identifies the datastore associated with the events to be handled.
    // Used to ensure that this datastore matches the one this build supports.
    String datasetStoreId = System.getenv(ENV_DATASTORE_ID);

    String mode = System.getenv(ENV_RUN_MODE);

    logger.info("Parameters - Project(s): " + projectIds
      + ", Dataset Store: " + datasetStoreId
      + ", Run Mode: " + mode);

    switch (mode) {
      case "sync":
        syncMode(projectIds, datasetStoreId);
        break;
      case "cleanup":
        cleanupMode(projectIds);
        break;
      default:
        logger.error("Unset or invalid RUN_MODE value.  Must be one of \"sync\" or \"cleanup\".");
    }
  }

  private static void syncMode(List<String> projectIds, String datasetStoreId) throws WdkModelException {
    var eventJsonArray = new LinkedList<UDEvent>();

    // Create a dataset event handler to process the resulting events list.
    // The dataset event handler constructor uses the provided projectId
    // to initialize and populate the user dataset store and provide the
    // temporary directory url.
    var handler = new UserDatasetEventSync(projectIds);
    var dsStore = handler.getUserDatasetStore();

    // Open the user dataset session for processing the event list.
    try(UserDatasetSession dsSession = dsStore.getSession(dsStore.getUsersRootDir())) {

      // Ensure that the dataset store that triggered this event handling
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
      handler.handleEventList(
        UserDatasetEventSync.parseEventsArray(eventJsonArray),
        getMaxEventsPerExecution()
      );
    }
  }

  private static void cleanupMode(List<String> projectIds) throws WdkModelException {
    new UserDatasetEventCleanup(projectIds).cleanupFailedInstalls();
  }

  /**
   * Parses the {@link ProcessIrodsEvents#ENV_MAX_EVENTS} environment variable
   * into an int value, or defaults to
   * {@link ProcessIrodsEvents#DEFAULT_MAX_EVENTS_PER_EXEC}.
   *
   * This value controls the max number of iRODS events that will be processed
   * in a single execution of this script.
   *
   * @return Maximum number of events to handle in a single script execution.
   */
  private static int getMaxEventsPerExecution() {
    String env = System.getenv(ENV_MAX_EVENTS);

    if (env == null || env.isBlank())
      return DEFAULT_MAX_EVENTS_PER_EXEC;

    try {
      return Integer.parseInt(env);
    } catch (Throwable e) {
      logger.warn("MAX_EVENTS was not a valid int value, defaulting to " + DEFAULT_MAX_EVENTS_PER_EXEC);
      return DEFAULT_MAX_EVENTS_PER_EXEC;
    }
  }
}
