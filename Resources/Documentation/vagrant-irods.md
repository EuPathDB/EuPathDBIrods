# How to Set Up a Full IRODS Env for WDK on Vagrant

These steps are based upon the contents of the EuPathDBIrods project which is found in the [svn repository](https://www.cbil.upenn.edu/svn/apidb/EuPathDBIrods/trunk/).  This document is very preliminary and subject to change - possibly considerable change.  So stay tuned.

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
 plas	PlasmoDB
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
  * Go to the user's configuration page and show and record the API token.  Will need it later.
  
### Create a Jenkins node for IRODS.
  * This mirrors the typical production Jenkins setup.
  * The menu path is <code>Manage Jenkins | Manage Nodes | New Node</code>.
  * The node name is irods.
  * Select permanent agent and click OK.
  * Choose as many executors as you have projects since each listener blocks identical listeners but different listeners can run concurrently.
  * Select for Usage, 'Use this node as much as possible'.
  * Select for Launch method, 'Launch slave agents via SSH'.
  * Select for Availability, 'Keep this agent online as much as possible'.
  * The remote root directory is <code>/var/tmp</code>.
  * The node user is joeuser and the node name is irods.  Again consult the link above for a setup guide.
  * The workspace will be in <code>/var/tmp</code>.
  
###  Create IRODS scaffold
  *  A copy of the scaffold is found in the EuPathDBIrods project (<code>cp /vagrant/scratch/project_home/EuPathDBIrods/Resources/scaffold.tar.gz ~.</code>).
  *  Unpack it (<code>tar -xvf scaffold.tar.gz</code>).
  *  Create the scafford (<code>irsync -r workspaces i:/ebrc/workspaces</code>).
  *  This IRODS scraffold has no users to start with but does have a landing zone (lz) and an events folder sibling to users
  
### Set Up IRODS User Home Directory
  * <code>cd ~/.irods</code> and edit irods_environment.json.
  * Add <code>"irods_home": "/ebrc/workspaces"</code>
  * Remember to add a comma where appropriate to insure proper json syntax.
  
### Generate Jenkins Jobs
  * To generate the Jenkins Jobs, we will follow the procedure described in the <code>JenkinsSetup.md</code> that comes with the vagrant-wij package with a few alterations.
  * Insure that all the needed plugins are installed.
  * Outside of vagrant, copy the generator script for the irods jobs from the EuPathDBIrods project into the vagrant directory (<code>cp scratch/project_home/EuPathDBIrods/Resources/JenkinsJobs/irodsWorkspacesJobs.groovy .</code>).
  * Rather than follow pasting the Groovy script described in the markdown document, paste into the Jenkins Script Console (under Manage Jenkins), the script found at <code>project_home/EuPathDBIrods/Resources/JenkinsJobs/irodsJobGenerator.txt</code>.
  * That script will create a shared workspace in /var/tmp/jenkins-irods.
  * In vagrant, become joeuser (<code>sudo su - joeuser</code>) and go to the new workspace (<code>cd /var/tmp/jenkins-irods</code>).
  * As joeuser, copy the PlasmoDBMetaConfig.yaml file described earlier into this workspace (e.g.,<code>cp /vagrant/scratch/PlasmoDBMetaConfig.yaml /var/tmp/jenkins-irods/.</code>).
  * As joeuser, copy the gus configuration file (gus.config) into this workspace (e.g., <code>cp /vagrant/scratch/gus.config /var/tmp/jenkins-irods/.</code>).
  * As joeuser, copy the text file containing the supported projects, projectList.txt into this workspace (e.g., <code>cp /vargrant/scratch/projectList.txt /var/tmp/jenkins-irods/.</code>).
  * On the Jenkins website, run the irods-job-generator.  The build should create an irods-builder, an irods-listener, and as many irods-handler-[project] jobs as there are project supported in the irodsWorkspacesJob.groovy script.

### Set Up Subversion
  * Jenkins 2 uses the default SVN version of 1.4.
  * On the Jenkins website (as admin), go to <code>Manage Jenkins ->  Configure System</code> and change the Subversion version to 1.8.
  
### Allow DB Connections Through Firewall
  * Run sshuttle (<code>sshuttle -e 'ssh -o StrictHostKeyChecking=no' -r [user]@spruce.pcbi.upenn.edu 128.91.49.128/24 128.192.0.0/16 > /dev/null 2>&1 &</code>).
  * Insure that a process number is returned.  Remember to do this initially after vagrant up/vagrant ssh or builds will not work.
  
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
  
### Run the IRODS Builder Job
  * This job is parameterized with the username and password/token of the Jenkins user that will be calling the IRODS listener job from within the IRODS ecosystem.
  * A third parameter, MODE, defaults to Dev.  Put anything else in its place to force a clean and complete rebuild of the shared workspace.  Note that the clean removes gus_home and project_home, but not the template files copies over from <code>/vagrant/scratch</code>.
  * This job will check out from svn, the 17 projects needed for the other IRODS jobs.
  * Additionally, the job will use the template files to create model-config.xml and [project].gus.config files for every project supported (as determined by the projectList.txt file).
  * FInally, the job will create the jenkinsCommunicationConfig.txt. It is located in IRODS at <code>/ebrc/workspaces</code> and will be used by one of the python scripts mentioned above to communicate with the IRODS Listener (irods-listener) job on Jenkins.
  * It would be prudent to be sure that file was created and properly placed.
  
### End to End Testing
  * A sample dataset (<code>dataset_u12401223_t1231238088881.tgz</code>) is available in the EuPathDBIrods project for testing.  Copy it over to vagrant home (<code>cd ~</code> and <code>sudo cp /vagrant/scratch/project_home/EuPathDBIrods/Resources/dataset_u12401223_t1231238088881.tgz .</code>).
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
  * Since joeuser has full access to the project_home under /var/tmp/jenkins-irods, we can set this user up to have IRODS access also.
  * Become joeuser (<code>sudo su - joeuser</code>).  The home directory will be <code>/usr/local/home/joeuser</code>.
  * Follow the instructions in Setup IRODS User above to give joeuser IRODS access.
  * Add a proper IRODS home directory also, as described in Setup IRODS User Home Directory.
  * Create a setenv file in joeuser's home dir:
  
<code>
	export BASE_GUS=/var/tmp/jenkins-irods
	export GUS_HOME=$BASE_GUS/gus_home
	export PROJECT_HOME=$BASE_GUS/project_home
	export PATH=$GUS_HOME/bin:$PROJECT_HOME/install/bin:$MVN_HOME/bin:$PATH
	export PERL5LIB=$GUS_HOME/lib/perl
	export PROJECT_ID=PlasmoDB
</code>	  

  * The PROJECT_ID environmental variable can be any project supported by this application.
  * Add a DATASET_SOURCE_ID environment variable and set it to the last entry in the comma delimited line found in the jenkinsCommunicationsConfig.txt file.
  
### Alter Source Code Location
  * The only source code likely to be changed for development will be EuPathDBIrods, WDK, and FgpUtil.
  * Consequently, as joeuser, remove those projects from project_home in the workspace.
  
<code>
   source setenv
   rm -rf $PROJECT_HOME/WDK
   rm -rf $PROJECT_HOME/FgpUtil
   rm -rf $PROJECT_HOME/EuPathDBIrods
</code>

  * Outside of vagrant, create a project_home directory inside this vagrant's scratch directory and checkout WDK and FgpUtils alongside EuPathDBIrods into that project_home folder.
  * For convenience one can create a new Eclipse workspace pointing to this project_home so that the IDE may be used to modify code.
  * Inside vagrant, as joeuser symlink to these 3 projects from inside the project_home of the Jenkins IRODS workspace.

<code>
	cd $PROJECT_HOME
	ln -s /vagrant/scratch/project_home/WDK WDK
	ln -s /vagrant/scratch/project_home/FgpUtil FgpUtil
	ln -s /vagrant/scratch/project_home/EuPathDBIrods EuPathDBIrods
</code>	

###   Using this Development Environment
  * As the vagrant user, make sure to run sshuttle to permit DB access - see Allow DB Connections Through Firewall above.
  * Build any Java code changes manually from within the project_home in the Jenkins IRODS workspace (e.g., <code>bld EuPathDBIrods/Controller</code>).
  * As joeuser, one can run the Irods handler jobs (irods-handler-[project]) outside of Jenkins by simply running <code>fgpJava org.apidb.irods.EuPathDBIrods</code>.  The project id and the dataset_source_id are provided by environmental variables that were set in the setenv script.
  * One can still run any Irods handler job (irods-handler-[project]) directly from Jenkins, filling in the required DATASET_SOURCE_ID parameter at that point.  One can also run the Irods listener job (irods-listener) directly from Jenkins, again filling in the required DATASET_SOURCE_ID parameter.
  * The log4j.properties under $GUS_HOME/config is the location of the log4j configuration and it currently set to log any org.gusdb or org.apidb logging statement with a priority level of INFO or greater.
  * Since jobuser is the same IRODS user as vagrant, the iput command in the End to End Testing section should apply equally well here.
	  
  
  
  
  
  

  
  
