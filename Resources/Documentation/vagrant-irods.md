# How to Set Up a Full IRODS Env for WDK on Vagrant

These steps are based upon the contents of the EuPathDBIrods project which is found in the [svn repository](https://www.cbil.upenn.edu/svn/apidb/EuPathDBIrods/trunk/).  This document is very, very preliminary and subject to change - possibly considerable change.  So stay tuned.

### Install and Start Up Vagrant
  * Insure that the vagrant is properly provisioned.  Using [vagrant-wij](https://github.com/EuPathDB/vagrant-wij)
  *	Make sure to install the landrush and vagrant-libraries-puppet plugins.  The link above explains how.
  *	<code>vagrant up</code> and <code>vagrant ssh</code> to start.
  * Starting up vagrant the first time needs to take place on campus to avoid firewall issues.
  
### Create Configuration Files
  * Outside of vagrant, in its associated scratch directory, create a PlasmoDBMetaConfig.yaml file.  It will serve as a template for creating other project metaConfigure yaml files.  Remember that the userDatasetStore should be correctly populated with the information needed to access the irods system that will be calling the Jenkins job.
  * Create, in the same directory, a gus.config file for the PlasmoDB project.  It too, will serve as a template for creating additional [project].gus.config files for all the projects to be supported.
  * Create, in the same directory, a file, projectList.txt.  It will contain all the projects to be supported by the Jenkins IRODS Build and will be formatted with the database prefix and the project id separated by a tab.  For example:
  
 <code>
 plas	PlamsoDB
 toxo	ToxoDB
 </code>	  

  * In scratch, create a project_home directory.
  * In the project_home dir, checkout from svn, the EuPathDBIrods project (<code>svn checkout https://www.cbil.upenn.edu/svn/apidb/EuPathDBIrods/trunk project_home/EuPathDBIrods</code>). 
  * The files located in this scratch directory are available within vagrant.  A number of these files will be needed later.
  
### Set Up IRODS User
  * In the vagrant home dir do <code>iinit</code> for wrkspuser/passWORD
  * The answers to the questions should match those properties of the userDataetStore in the yaml file (in the scratch dir) that will be employed here.
  * This will allow vagrant user to mirror WDK use as these are the credentials that the WDK will use.
  
### Start Up Jenkins
  * Jenkins runs as a service.  If not running, start it (consult the vagrant-wij README.md file for details)
  * The website is <code>wij.vm:9171</code>
  * Unlock Jenkins with password as explained on the website
  * Create a Jenkins admin user
  
### Set Up a Jenkins User to IRODS Jobs
  * As the admin user, create a wrkspuser (use the same IRODS password for convenience).
  * Log off as admin and log on as wrkspuser.
  * Go to the configuration page and show and record the API token.  Will need it later.
  
### Create a Jenkins node for IRODS.
  * This mirrors the typical production Jenkins setup.
  * The node user is joeuser.  Again consult the link above for a setup guide.
  * The workspace will be in <code>/var/tmp</code>.
  
###  Create IRODS scaffold
  *  A copy of the scaffold is found in the EuPathDBIrods project (<code>cp /vagrant/scratch/EuPathDBIrods/Configurations/scaffold.tar.gz ~</code>).
  *  Unpack it (<code>tar -xvf scaffold.tar.gz</code>).
  *  Create the scafford (<code>irsync -r workspaces i:/ebrc/workspaces</code>).
  *  This IRODS scraffold has no users to start with but does have a landing zone (lz) and an events folder sibling to users
  
### Set Up IRODS User Home Directory
  * <code>cd ~/.irods</code> and edit irods_environment.json.
  * Add <code>"irods_home": "/ebrc/workspaces"</code>
  * Remember to add a comma where appropriate to insure proper json syntax.
  
### Load Jenkins Jobs
  * Become the Jenkins user (note Jenkins does not have a login shell <code>sudo su -s /bin/bash jenkins</code>).
  * Go to the Jenkins jobs directory (<code>cp /usr/local/home/jenkins/Instances/WS/jobs</code>).
  * Set up job directories for each job (<code>mkdir IrodsBuilder IrodsListener</code>).
  * Add each of the three build configurations to its respective folder as config.xml.  They are found in the EuPathDBIrods project (e.g., <code>cp /vagrant/scratchEuPathDBIrods/Configurations/JenkinsJobs/IrodsBuilder.xml config.xml</code>).
  * Log off as jenkins (<code>exit</code>).
  * On the Jenkins website (as admin), go to <code>Manage Jenkins -> Reload Configuration from Disk</code>
  
### Set Up Subversion
  * Jenkins 2 uses the default SVN version of 1.4.
  * On the Jenkins website (as admin), go to <code>Manage Jenkins ->  Configure System</code> and change the Subversion version to 1.8.
  
### Allow DB Connections Through Firewall
  * Run sshuttle (<code>sshuttle -e 'ssh -o StrictHostKeyChecking=no' -r [user]@spruce.pcbi.upenn.edu 128.91.49.128/24 128.192.0.0/16 > /dev/null 2>&1 &</code>).
  * Insure that a process number is returned.  Remember to do this initially after vagrant up/vagrant ssh or builds will not work.
  
### Verify Jobs
  * For each of the jobs, IrodsBuilder and IrodsListener, verify that each is restricted to run on the irods node and set it if otherwise.
  
### Set Up Irods Builder Jenkins Job
  * Run the IrodsBuilder job manually - via Build Now button.  It will fail but this action will create a workspace for the job at <code>/var/tmp/workspace/IrodsBuilder</code>
  * Become joeuser (<code>sudo su - joeuser</code>) and go to the new workspace (<code>cd /var/tmp/workspace/IrodsBuilder</code>)
  * As joeuser, copy the PlasmoDBMetaConfig.yaml file described earlier into the IrodsBuilder workspace (e.g.,<code>cp /vagrant/scratch/PlasmoDBMetaConfig.yaml /var/tmp/workspace/IrodsBuilder/.</code>).
  * As joeuser, copy the gus configuration file (gus.config) into the IrodsBuilder workspace (e.g., <code>cp /vagrant/scratch/gus.config /var/tmp/workspace/IrodsBuilder/.</code>).
  * As joeuser, copy the text file containing the supported projects, projectList.txt into the IrodsBuilder workspace (e.g., <code>cp /vargrant/scratch/projectList.txt /var/tmp/workspace/IrodsBuilder/.</code>).
  * Log off as joeuser (<code>exit</code>).
  * Return to the Jenkins website and run the IrodsBuilder job again.  It should be successful this time.
  * The parameter MODE defaults to Dev.  Set it to anything else to do a full clean, full checkout and site rebuild.
  
### Set Up IRODS Microservices
  * Copy the file containing the IRODS microservices from the EuPathDBIrods project to the location where IRODS would expect it (<code>sudo /var/tmp/workspace/IrodsBuilder/project_home/EuPathDBIrods/Scripts/ud.re /etc/irods/.</code>).
  * Go to that location (<code>/etc/irods</code>) and change the owner to irods (<code>sudo chown irods.irods /etc/irods/ud.re</code>).
  * In that location, edit the server_config.json file as shown (it may be wise to create a backup first):  
<code>
	  "re\_rulebase\_set": [
	          {
	              "filename": "ud"
	          },
	          {
	              "filename": "ebrc"
	          }
	      ,
</code>

  * Note that editing must be done also with sudo.
  * Any syntax errors in ud.re can very easily compromise the IRODS system so check by issuing a simple irods command (e.g., <code>ils</code>).
  
### Set Up External Python Scripts Used By IRODS Microservices
  * Some of the more involved (for microservices) operations are handled by Python scripts, housed in <code>/var/lib/irods/iRODS/server/bin/cmd</code>, which are executable, and are owned by IRODS.
  * Those scripts are available in the EuPathDBIrods project.
  * Copy over those scripts (<code>sudo cp /var/tmp/workspace/IrodsBuilder/project_home/EuPathDBIrods/Scripts/remoteExec/*.py /var/lib/irods/iRODS/server/bin/cmd/*.py</code>).
  * Make them executable (<code>sudo chmod 755 /var/lib/irods/iRODS/server/bin/cmd/*.py</code>)
  * Make them owned by IRODS (<code>sudo chown irods.irods /var/lib/irods/iRODS/server/bin/cmd/*.py</code>).
  
### Set Up IRODS - Jenkins Communication Configuration File
  * This file, jenkinsCommunicationConfig.txt is actually created during the IrodsBuilder build step.
  * It is located in IRODS at <code>/ebrc/workspaces</code> and will be used by one of the python scripts mentioned above to communicate with the IRODSListener job on Jenkins.
  * It would be prudent to be sure that file was created and properly placed.
  
### Set Up the IRODS Listener Jenkins Job
  *  Run the IrodsListener job manually - via Build Now button.  It will fail but this action will create a workspace for the job at <code>/var/tmp/workspace/IrodsListener</code>
  * Become joeuser (<code>sudo su - joeuser</code>) and go to the new workspace (<code>cd /var/tmp/workspace/IrodsListener</code>).
  * Create a <code>setenv</code> bash script file here containing the following:
  
<code>
	 export BASE_GUS=/var/tmp/workspace/IrodsBuilder
	 export GUS_HOME=$BASE_GUS/gus_home
	 export PROJECT_HOME=$BASE_GUS/project_home
	 export MVN_HOME=/usr/java/maven-3.3.3
	 export PATH=$GUS_HOME/bin:$PROJECT_HOME/install/bin:$MVN_HOME/bin:$PATH
	 export PERL5LIB=$GUS_HOME/lib/perl
	 export M2_REPO=$PROJECT_HOME/.m2_repository
</code>

  * This bash script differs from the one for IrodsBuilder only in that the BASE_GUS is specified here.  BASE_GUS points to the IrodsBuilder workspace as that is where the actual project resides.
  * Log off as joeuser (<code>exit</code>)
  * Return to the Jenkins website and run the IrodsListener job again.  It should be successful this time.
  
### End to End Testing
  * A sample dataset (<code>dataset_u12401223_t1231238088881.tgz</code>) is available in the EuPathDBIrods project for testing.  Copy it over to vagrant home (<code>cd ~</code> and <code>sudo c /var/tmp/workspace/IrodsBuilder/Resources/dataset_u12401223_t1231238088881.tgz .</code>).
  * Be careful - it is easy to inadvertantly run Unix commands rather than iCommands.
  * Go to the IRODS landing zone (<code>icd /ebrc/workspaces/lz</code>)
  * Put this dataset into the landing zone (<code>iput dataset_u12401223_t1231238088881.tgz</code>)
  * Go to the IRODS users collection and examine the contents.  Assuming a virgin installation, a new user whose id is 12401223 will have been created.
  * Go to the IRODS collection for that user and observe a datasets collection within it.
  * Go to that IRODS datasets collection and observe a collection for the new dataset with a unique id.
  * Go to the IRODS collection for that dataset and observe that all the expected files are present.  One can do <code>iget</code> for the various files to create local copies for assessment.
  * Go to /ebrc/workspaces/events and note that, in the case of a virgin install, a single event file exists.  Do an <code>iget</code> on that file to obtain a local copy and verify that it has the correct information given the dataset and the action taken.
  * Go to the Jenkins website dashboard and observe that the successful build count has increased by the number of job builds called by the jenkinsCommunicationConfig.txt (i.e., one job runs for each project).
  * Connect the the ApiDBUserDatasets schema for each project instance provided in the projectList.txt and insure that the event was properly captured and the dataset was properly parsed.  The sample dataset includes a gene list.  The list is only relevant for PlamsoDB, but that should not prevent its inclusion in other database instances.
  
# How to Develop in this Env

Note that these modifications assume that the setup described in How to Set Up a Full IRODS Env for WDK on Vagrant is complete and correct.  These changes are not appropriate for production release.

### Modify Jenkins User
  * Since joeuser has full access to the project_home under IrodsBuilder, we can set this user up to have IRODS access also.
  * Become joeuser (<code>sudo su - joeuser</code>).  The home directory will be <code>/usr/local/home/joeuser</code>.
  * Follow the instructions in Setup IRODS User above to give joeuser IRODS access.
  * Add a proper IRODS home directory also, as described in Setup IRODS User Home Directory.
  * Copy the setenv file in the IrodsListener workspace to joeuser home dir (<code>cp /var/tmp/workspaces/IrodsListener/setenv /user/local/home/joeuser</code>).
  * Modify this new setenv file to add the line <code>export PROJECT_ID=[projectId]</code> where projectId refers to a project supported in this build that the developer wants to use for development work (e.g., PlasmoDB).
  
### Alter Source Code Location
  * The only source code likely to be changed for development will be EuPathDBIrods, WDK, and FgpUtil.
  * Consequently, as joeuser, remove those projects from project_home in the IrodsBuilder workspace.
<code>
	  source setenv
	  rm -rf $PROJECT_HOME/WDK  
  	  rm -rf $PROJECT_HOME/FgpUtil
	  rm -rf $PROJECT_HOME/EuPathDBIrods

</code>

  * Outside of vagrant, create a project_home directory inside this vagrant's scratch directory and checkout this 3 projects into that project_home folder.
  * For convenience one can create a new Eclipse workspace pointing to this project_home so that the IDE may be used to modify code.
  * Inside vagrant, as joeuser symlink to these 3 projects from inside the project_home of the IrodsBuilder workspace.
<code>
	cd $PROJECT_HOME
	ln -s /vagrant/scratch/project_home/WDK WDK
	ln -s /vagrant/scratch/project_home/FgpUtil FgpUtil
	ln -s /vagrant/scratch/project_home/EuPathDBIrods EuPathDBIrods
	
</code>	

###   Using this Development Environment
  * As the vagrant user, make sure to run sshuttle to permit DB access - see Allow DB Connections Through Firewall above.
  * As joeuser, one can run the Irods Listener code outside of Jenkins by simply running <code>fgpJava org.apidb.irods.EuPathDBIrods</code>.  The project id is provided by an environmental variable that was set in the setenv script.
  * One can still run Irods Listener from Jenkins.
  * The log4j.properties under $GUS_HOME/config is the location of the log4j configuration and it currently set to log any org.gusdb or org.apidb logging statement with a priority level of INFO or greater.
  * Since jobuser is the same IRODS user as vagrant, the iput command in the End to End Testing section should apply equally well here.
	  
  
  
  
  
  

  
  
