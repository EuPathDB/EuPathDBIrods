package org.apidb.irods;

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
import org.gusdb.wdk.model.user.dataset.UserDatasetStore;
import org.gusdb.wdk.model.user.dataset.UserDatasetStoreAdaptor;
import org.xml.sax.SAXException;

public class BuildJenkinsCommunicationFile {

  @SuppressWarnings("unused")
  private static final Logger logger = Logger.getLogger(BuildJenkinsCommunicationFile.class);
  private static final String TOP_LEVEL_DIR = "/ebrc/workspaces";
  private static final String JENKINS_COMMUNICATION_FILE = "jenkinsCommunicationConfig.txt";
  private static final String NL = System.lineSeparator();

  public static void main(String[] args) throws Exception {
	final CommandLineParser cmdLineParser = new PosixParser();
    final Options cmdOptions = new Options();
    cmdOptions.addOption("u",true,"Name of Jenkins User");
    cmdOptions.addOption("p",true,"Token for Jenkins User");
    cmdOptions.addOption("j",true,"Url of Jenkins Job");
    cmdOptions.addOption("t",true,"Jenkins Job Token");
    cmdOptions.addOption("l",true,"Comma delimited list of Supported Projects");
    CommandLine commandLine;
    String username = null;
    String password = null;
    String job = null;
    String token = null;
    String projectList = null;
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
    	projectList = commandLine.getOptionValue("l");
      }
    }
    catch (ParseException pe) {
      throw new RuntimeException(pe);  
    }
    if(username == null || password == null || job == null || token == null || projectList == null) {
      throw new RuntimeException("Some required parameters were not specified");
    }
    String[] projects = projectList.split(",");
    String gusHome = System.getProperty(Utilities.SYSTEM_PROPERTY_GUS_HOME);     
    ModelConfigParser parser = new ModelConfigParser(gusHome);
    ModelConfig modelConfig = null;
    try {
  	  modelConfig = parser.parseConfig(projects[0]);
  	} 
  	catch(WdkModelException | SAXException | IOException e) {
  	  e.printStackTrace();
  	  throw new RuntimeException(e);
  	}
    StringBuilder contents = new StringBuilder();
    ModelConfigUserDatasetStore udsConfig = modelConfig.getUserDatasetStoreConfig();
    UserDatasetStore uds = udsConfig.getUserDatasetStore();
    String userDatasetStoreId = uds.getUserDatasetStoreId();
    contents.append(username + "," + password + "," + job + "," + token + "," + userDatasetStoreId + NL);
	for(String project : projects) {
	  contents.append(project + NL);
	}
	UserDatasetStoreAdaptor udsa = uds.getUserDatasetStoreAdaptor();
	udsa.writeFile(Paths.get(TOP_LEVEL_DIR, JENKINS_COMMUNICATION_FILE), contents.toString(), false);
  }
}
