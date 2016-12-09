# How to Set Up a Full IRODS Env for WDK on Vagrant

These steps are based upon the contents of the EuPathDBIrods project which is found at https://www.cbil.upenn.edu/svn/apidb/EuPathDBIrods/trunk/.  This document is very, very, very, very preliminary and subject to change - possibly considerable change.  So stay tuned.

### Install and Start Up Vagrant
  * Insure that the vagrant is properly provisioned.  Using vagrant-wij (https://github.com/EuPathDB/vagrant-wij)
  *	Make sure to install the landrush and vagrant-librariea-puppet plugins.  The link above explains how.
  *	<code>vagrant up</code> and <code>vagrant ssh</code> to start.
  * Starting up vagrant the first time needs to take place on campus to aviod firewall issues.
### Set Up IRODS User
  * in vagrant home dir do <code>iinit</code> for wrkspuser/passWORD
  * this will allow vagrant user to mirror WDK use as these are the credentials that the WDK will use.
### Start Up Jenkins
  * Jenkins runs as a service.  If not running, start it (consult the vagrant-wij README.md file for details)
  * The website is wij.vm:9171
  * Unlock Jenkins with password as explained on the website
  * Create a Jenkins admin user
### Set Up a Jenkins User to IRODS Jobs
  * As the admin user, create a wrkspuser (use the same IRODS password for convenience).
  * Log off as admin and log on a wrkspuser.
  * On to the configuration page and show the API token.  Will need it later.
### Create a Jenkins node for IRODS.
  * This mirrors the typical production Jenkins setup.
  * The node user is joeuser.  Again consult the link above for a setup guide.
  * The workspace will be in /var/tmp.
###  Create IRODS scaffold
  *  Copy the IRODS scaffold from EuPathDBIrods/Resources/scaffold.tar.gz into the scratch directory for this vagrant to make it accessible to the vagrant instance.
  *  <code>cp /vagrant/scratch/scaffold.tar.gz ~</code> and <code>tar -xvf scaffold.tar.gz</code>
  *  <code>irsync -r workspaces i:/ebrc/workspaces</code> to create the scaffold.
  *  This IRODS scraffold has no users but does have a landing zone (lz) and an events folder sibling to users
### Set Up IRODS User Home Directory
  * <code>cd ~/.irods</code> and edit irods_environment.json.
  * Add <code>"irods_home": "/ebrc/workspaces/"</code>
  * Remember to add a comma where appropriate to insure proper json syntax.
### Load Jenkins Jobs
  * Copy the IRODSBuilder.xml, IRODSCleaner.xml and IRODSListener.xml from EuPathDBIrods/Resources/JenkinsJobs into the scratch directory for this vagrant to make them accessible to the vagrant instance.
  * Become the Jenkins user (note Jenkins does not have a login shell) with <code>sudo su -s /bin/bash jenkins</code>
  * Go to the Jenkins jobs directory: <code>cp /usr/local/home/jenkins/Instances/WS/jobs</code>
  * <code>mkdir IrodsBuilder IrodsCleaner IrodsListener</code> to set up job directories for each job.
  * Add each of the three build configurations to its respective folder as config.xml (e.g., <code>cp /vagrant/scratch/IrodsBuilder.xml config.xml</code>)
  * Log off as jenkins (<code>exit</code>).
  * On the Jenkins website (as admin), go to <code>Manage Jenkins -> Reload Configuration from Disk</code>
### Set Up Subversion
  * Jenkins 2 uses the default SVN version of 1.4.
  * On the Jenkins website (as admin), go to <code>Manage Jenins ->  Configure System</code> and change the Subversion version to 1.8
### Verify Jobs
  * For each of the jobs, IrodsBuilder, IrodsCleaner, IrodsListener, verify that each is restricted to run on the irods node and set it if otherwise.
### Set Up Irods Builder Jenkins Job
  * Run the IrodsBuilder job manually - via Build Now button.  It will fail but this action will create a workspace for the job at <code>/var/tmp/workspace/IrodsBuilder</code>
  * Become joeuser: <code>sudo su - joeuser</code> and go to the new workspace <code>cd /var/tmp/workspace/IrodsBuilder</code>
  * Create a <code>setenv</code> bash script file here containing the following:
<code>
  export GUS_HOME=$BASE_GUS/gus_home
  export PROJECT_HOME=$BASE_GUS/project_home
  export MVN_HOME=/usr/java/maven-3.3.3
  export PATH=$GUS_HOME/bin:$PROJECT_HOME/install/bin:$MVN_HOME/bin:$PATH
  export PERL5LIB=$GUS_HOME/lib/perl
  export M2_REPO=$PROJECT_HOME/.m2_repository
  
</code>

  * Outside of vagrant, create those yaml metafiles need for those projects to be supported by the Jenkins IRODS jobs.  Follow the file naming convention modelDBMetaConfigure.yaml (e.g., <code>plasmoDBMetaConfigure.yaml</code>)
  * Edit as necessary to insure that the user dataset information is appropriate for the irods instance (credentials and location).
  * Move those yaml metafiles into the /vagrant/scratch directory.
  * As joeuser, copy each of these yaml metafiles into the IrodsBuilder workspace (e.g.,<code>cp /vagrant/scratch/plasmoDBMetaConfigure.yaml /var/tmp/workspace/IrodsBuilder/.</code>).
  * Log off as joeuser (<code>exit</code>).
  * Return to the Jenkins website and run the IrodsBuilder job again.  It should be successful this time.
### Set Up IRODS Microservices
  * Copy the file containing the IRODS microservices from the EuPathDBIrods project to the location where IRODS would expect it (<code>sudo /var/tmp/workspace/IrodsBuilder/project_home/EuPathDBIrods/Scripts/ud.re /etc/irods/.</code>).
  * Go to that location (<code>/etc/irods</code>) and change the owner to irods (<code>sudo chown irods.irods /etc/irods/ud.re</code>).
  * In that location, edit the server_config.json file as shown (it may be wise to create a backup first):  
<code>
	  "re_rulebase_set": [
	          {
	              "filename": "ud"
	          },
	          {
	              "filename": "ebrc"
	          }
	      ,

</code>

  * Note that editing must be done also with sudo.
  * Any syntax errors in ud.re can very easily compromise the IRODS system so check by issuing a simple irods command (e.g., <code>ils</code>)
### Set Up External Python Scripts Used By IRODS Microservices
  * Some of the more involved (for microservices) operations are handled by Python scripts, which are housed in <code>/var/lib/irods/iRODS/server/bin/cmd</code>, are executable, and are owned by IRODS.
  * Copy over those scripts (<code>sudo cp /var/tmp/workspace/IrodsBuilder/project_home/EuPathDBIrods/Scripts/remoteExec/*.py /var/lib/irods/iRODS/server/bin/cmd/*.py</code>)
  * Make them executable (<code>sudo chmod 755 /var/lib/irods/iRODS/server/bin/cmd/*.py</code>)
  * Make them owned by IRODS (<code>sudo chown irods.irods /var/lib/irods/iRODS/server/bin/cmd/*.py</code>)
### Set Up IRODS - Jenkins Linkage File
  * Use <code>ils</code> to insure that the current IRODS collection is <code>/ebrc/workspaces</code>.  Perform <code>icd /etc/workspaces</code> to get there, otherwise.
  * Put the linkage file into this IRODS wrkspuser home collection (<code>iput /var/tmp/workspace/Irods/Builder/project_home/EuPathDBIrods/Scripts/jobFile.txt</code>).
  * The name jobFile.txt is subject to change.
### Set Up the IRODS Listener Jenkins Job
  *  Run the IrodsListener job manually - via Build Now button.  It will fail but this action will create a workspace for the job at <code>/var/tmp/workspace/IrodsListener</code>
  * Become joeuser: <code>sudo su - joeuser</code> and go to the new workspace <code>cd /var/tmp/workspace/IrodsListener</code>
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
  * Go to the Jenkins website dashboard and observe that the successful build count has increased by the number of job builds called by the jobFile.txt (i.e., one job runs for each project).
  * Presently, the data only goes to the console output.  But opening the console output should display the single line entries for all the events in the events folder, each prepended with a timestamp.  In the case of a virgin run, only 1 event will appear.
  
  
  	  
	  
  
  
  
  
  

  
  
