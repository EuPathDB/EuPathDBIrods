package org.apidb.irods;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.apache.commons.cli.PosixParser;
import org.apache.log4j.Logger;
import org.gusdb.wdk.model.Utilities;
import org.gusdb.wdk.model.WdkModelException;
import org.gusdb.wdk.model.config.ModelConfig;
import org.gusdb.wdk.model.config.ModelConfigParser;
import org.gusdb.wdk.model.config.ModelConfigUserDatasetStore;
import org.gusdb.wdk.model.user.dataset.UserDatasetSession;
import org.gusdb.wdk.model.user.dataset.UserDatasetStore;
import org.gusdb.wdk.model.user.dataset.UserDatasetStoreAdaptor;
import org.xml.sax.SAXException;

/**
 * This is a small application intended to be run at the end of a Jenkins IRODS build.  It creates
 * a jenkinsCommunicationConfig.txt file and stuffs it into IRODS at a place sibling to the user
 * dataset root directory.  The file provides the information needed by IRODS to communicate events
 * back to the Jenkins IRODS listener job.  This can also be used on the command line as the needed
 * parameters are passed in.
 * @author crisl-adm
 *
 */
public class BuildJenkinsCommunicationFile {

  @SuppressWarnings("unused")
  private static final Logger logger = Logger.getLogger(BuildJenkinsCommunicationFile.class);
  private static final String JENKINS_COMMUNICATION_FILE = "jenkinsCommunicationConfig.txt";

  public static void main(String[] args) throws Exception {
	final CommandLineParser cmdLineParser = new PosixParser();
    final Options cmdOptions = new Options();
    cmdOptions.addOption("u",true,"Name of Jenkins User");
    cmdOptions.addOption("p",true,"Token for Jenkins User");
    cmdOptions.addOption("j",true,"Url of Jenkins Job");
    cmdOptions.addOption("t",true,"Jenkins Job Token");
    cmdOptions.addOption("l",true,"An Example Supported Project");
    CommandLine commandLine;
    String username = null;
    String password = null;
    String job = null;
    String token = null;
    String project = null;
    try {
      commandLine = cmdLineParser.parse(cmdOptions, args);
      if(commandLine.hasOption("u")) {
        username = commandLine.getOptionValue("u");
      }
      if(commandLine.hasOption("p")) {
        password = commandLine.getOptionValue("p");
      }
      if(commandLine.hasOption("j")) {
        job = commandLine.getOptionValue("j");
      }
      if(commandLine.hasOption("t")) {
    	token = commandLine.getOptionValue("t");
      }
      if(commandLine.hasOption("l")) {
    	project = commandLine.getOptionValue("l");
      }
    }
    catch (ParseException pe) {
      throw new RuntimeException(pe);  
    }
    if(username == null || password == null || job == null || token == null || project == null) {
      throw new RuntimeException("Some required parameters were not specified");
    }
    
    // We need to choose one of the model-config.xml files to parse.  So we need to pass in one of
    // the projects supported so as to locate one of these config files.
    String gusHome = System.getProperty(Utilities.SYSTEM_PROPERTY_GUS_HOME);     
    ModelConfigParser parser = new ModelConfigParser(gusHome);
    ModelConfig modelConfig = null;
    try {
  	  modelConfig = parser.parseConfig(project);
  	} 
  	catch(WdkModelException | SAXException | IOException e) {
  	  e.printStackTrace();
  	  throw new RuntimeException(e);
  	}
    StringBuilder contents = new StringBuilder();

    ModelConfigUserDatasetStore dsConfig = modelConfig.getUserDatasetStoreConfig();
    UserDatasetStore dsStore = dsConfig.getUserDatasetStore();
    try(UserDatasetSession dsSession = dsStore.getSession(dsStore.getUsersRootDir())) {	
    
      // The dataset store id is tacked onto the file being created so that it may be used to insure
      // that the IRODS instance using this file is that of the IRODS instance described in the file.
      String userDatasetStoreId = dsStore.getId();
      contents.append(username + "," + password + "," + job + "," + token + "," + userDatasetStoreId);
	  UserDatasetStoreAdaptor dsAdaptor = dsSession.getUserDatasetStoreAdaptor();

	  // In an effort to avoid hard-coding paths, grabbing the user dataset root dir from the id as it is
	  // guaranteed to always be the first (possibly only) item of a list of items delimited by a pipe.  The
	  // root directory applies to the users directory, but the Jenkins communication file is sibling to that
	  // directory.  Hence we use a relative address.
	  String userDatasetRootDir = userDatasetStoreId.split("\\|")[0];
	  String topLevelFilePath = userDatasetRootDir + File.separator + "..";
	  dsAdaptor.writeFile(Paths.get(topLevelFilePath, JENKINS_COMMUNICATION_FILE), contents.toString(), false);
    }
  }
}
