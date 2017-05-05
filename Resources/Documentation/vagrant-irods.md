# How to Set Up a Full IRODS Env for WDK on Vagrant
This setup is intended, at a minimum, as a proof of concept implementation ot the [Workspace Use Case and Specifications](https://docs.google.com/document/d/1GCq03dZz7y6WE7uzgWVphD8Tz1N0MWWNS1uD2g4huOQ/edit#heading=h.xrcnoy1kbpri) document.  These steps are based upon the contents of the EuPathDBIrods project which is found in the [svn repository](https://cbilsvn.pmacs.upenn.edu/svn/apidb/EuPathDBIrods/trunk/).  This document is less preliminary than it once was but still subject to change - hopefuly not considerable change.  This document was reasonably accurate as of 05MAY2017.

### Install and Start Up Vagrant
  * Insure that the vagrant is properly provisioned.  Using the irods 4.2 branch of [vagrant-wij](https://github.com/EuPathDB/vagrant-wij/tree/irods4.2).
  * Note that the VirtualBox manager app (version 5.1.14) and vagrant app (version 1.8.7) were used successfully in connection with this VM.  Other version combinations may not.
  *	Make sure to install the landrush and vagrant-libraries-puppet plugins.  The documentation in link above explains how.
  *	<code>vagrant up</code> and <code>vagrant ssh</code> to start.
  * Starting up vagrant the first time needs to take place on campus to avoid firewall issues as some content is downloaded from private repositories.
  
### Create Configuration Files
  * Outside of vagrant, in its associated scratch directory, create a PlasmoDBMetaConfig.yaml file.  It will serve as a template for creating other project metaConfigure yaml files.  Remember that the userDatasetStore should be correctly populated with the information needed to access the irods system that will be calling the Jenkins job.
  * Create, in the same directory, a gus.config file for the PlasmoDB project.  It too, will serve as a template for creating additional [project].gus.config files for all the projects to be supported.
  * For both of these configuration files the schema user is <code>ApidbUserDatasets</code>.  The databases used for testing have been plas-inc and toxo-inc.
  * Create, in the same directory, a file, projectList.txt.  It will contain all the projects to be supported by the Jenkins IRODS Build and will be formatted with the database prefix and the project id separated by a tab.  For example:
```txt
 plas	PlasmoDB
 toxo	ToxoDB
```

  * In scratch, create a project_home directory.
  * In the project_home dir, checkout from svn, the EuPathDBIrods project
```bash
svn checkout https://cbilsvn.pmacs.upenn.edu/svn/apidb/EuPathDBIrods/trunk/ project_home/EuPathDBIrods
```
  * The files located in this scratch directory are available within vagrant.  A number of these files will be needed later.
  
### Set Up IRODS User
  * In the vagrant home dir on the VM, do <code>iinit</code> for wrkspuser/passWORD
  * The answers to the questions should match those properties of the userDataetStore in the yaml file (in the scratch dir) that will be employed here.
  * This will allow vagrant user to mirror WDK use as these are the credentials that the WDK will use.
  
### Start Up Jenkins
  * Jenkins runs as a service.  If not running, start it (consult the vagrant-wij README.md file for details)
  * The website is <code>wij.vm:9171</code>
  * In this version of vagrant, Jenkins is pre-configured with an admin user.  Request the password from the sysadmins and insure that the login works.
  * This version of Jenkins comes with some plugins pre-installed.  We will indicate other plugin installations as needed.
  
### Set Up a Jenkins User to IRODS Jobs
  * As the admin user, create a wrkspuser (use the same IRODS password for convenience).
  * Log off as admin and log on as wrkspuser.
  * Go to the user's configuration page via <code>People | link in user table | Configure</code>.
  * Show and record the API token (<code>Show API Token...</code> button).  It will be needed later.
  
### Create a Jenkins node for IRODS.
  * This mirrors the typical production Jenkins setup.
  * The menu path is <code>Manage Jenkins | Manage Nodes | New Node</code>.
  * The node name is irods.
  * Select permanent agent and click OK.
  * Choose as many executors as you have projects since each listener blocks identical listeners but different listeners can run concurrently.
  * Select for Usage, 'Use this node as much as possible'.
  * Select for Launch method, 'Launch slave agents via SSH'.
  * The host is localhost.
  * When Adding creds, use 'joeuser' for the Username, 'SSH Username with private key' as Kind, 'System' as Scope, and 'From the Jenkins master ~/.ssh' as Private Key.
  * Select for Availability, 'Keep this agent online as much as possible'.
  * The remote root directory is <code>/var/tmp</code>.
  * Select for Host Key Verification Strategy, 'Non verifying Verification Strategy'
  * Consult the README.md that comes with the vagrant-wij download as these procedures are subject to change.
  
###  Create IRODS scaffold
  *  A copy of the scaffold is found in the EuPathDBIrods project.  Copy it into the vagrant home directory on the VM.
  ```bash
cp /vagrant/scratch/project_home/EuPathDBIrods/Resources/scaffold.tar.gz ~.
```
  *  Unpack it.
  ```bash
tar -xvf scaffold.tar.gz
```
  *  Create the scaffold.
  ```bash
irsync -r workspaces i:/ebrc/workspaces
```
  *  This IRODS scraffold has no users to start with but does have a landing zone (lz), a staging area, a flags collection, and an events collection sibling to the users collection.  Inside the users collection is a default_quota file that indicates the byte quota allowed per user.
  
### Set Up IRODS User Home Directory
  * On the VM, <code>cd ~/.irods</code> and edit irods_environment.json.
  * Add <code>"irods_home": "/ebrc/workspaces"</code>
  * Remember to add a comma where appropriate to insure proper json syntax.
  
### Generate Jenkins Jobs
  * Insure that the Pre SCM BuildStep Plugin is installed.  If not, install it via <code>Manage Jenkins | Manage Plugins</code>. 
  * Set up a seed job using this [tutorial](https://github.com/jenkinsci/job-dsl-plugin/wiki/Tutorial---Using-the-Jenkins-Job-DSL) as a guide.
  * Call the job 'irods-job-generator' and copy the content of <code>/vagrant/scratch/project_home/EuPathDBIrods/JenkinsJobs/irodsWorkspacesJobs.groovy</code> into the script entry area and click <code>Save</code>.
  * On the Jenkins website, run the irods-job-generator.  The build should create an irods-builder, an irods-listener, and as many irods-handler-[project] jobs as there are project supported in the irodsWorkspacesJob.groovy script.
  * Note that for every project to be supported, a <code>ApidbUserDatasets</code> schema must exist in the appropriate project stage (dev, prod, etc.) and be accessible.
  * In this version of Jenkins, groovy DSL scripts need to be approved.  The irods-listener is one such script.  Visit [Jenkins script approval](http://wij.vm:9171/scriptApproval/) page and approve the script it this becomes a problem.

### Seed Configuration Files Needed by Jenkins
  * In the VM, become joeuser.
  ```bash
sudo su - joeuser
```
  * As joeuser, copy the template project configuration file  (PlasmoDBMetaConfig.yaml), the gus configuration file (gus.config), and the text file containing the supported projects (projectList.txt) described earlier into this workspace.
  ```bash
cp /vagrant/scratch/PlasmoDBMetaConfig.yaml /var/tmp/jenkins-irods/.
cp /vagrant/scratch/gus.config /var/tmp/jenkins-irods/.
cp /vargrant/scratch/projectList.txt /var/tmp/jenkins-irods/.
```
* This is a stopgap measure to avoid manually editing the Jenkins workspace.  Better solutions are being sought.

### Set Up Subversion
  * Jenkins 2 uses the default SVN version of 1.4.
  * On the Jenkins website (as admin), go to <code>Manage Jenkins ->  Configure System</code> and change the Subversion version to 1.8.
  
### Allow DB Connections Through Firewall
  * Run sshuttle (<code>sshuttle -e 'ssh -o StrictHostKeyChecking=no' -r [user]@ash.pcbi.upenn.edu 128.91.49.128/24 128.192.0.0/16</code>) in a console window on the host.
  
### Set Up IRODS Microservices
  * Copy the file containing the IRODS microservices from the EuPathDBIrods project to the location where IRODS would expect it.
```bash
sudo cp /vagrant/scratch/project_home/EuPathDBIrods/Scripts/ud.re /etc/irods/.
```
  * Go to that location and change the owner and group to irods.
```bash
cd /etc/irods
sudo chown irods.irods /etc/irods/ud.re
```
  * In that location, edit the server_config.json file as shown (it may be wise to create a backup first):  
```json
	  "re\_rulebase\_set": [
	    "ud",
	    "ebrc",
		...
```

  * Note that editing must be done also with sudo.
  * Any syntax errors in ud.re can very easily compromise the IRODS system so check by issuing a simple irods command (e.g., <code>ils</code>).
  
### Set Up External Python Scripts Used By IRODS Microservices
  * Some of the more involved (for microservices) operations are handled by Python scripts, housed in <code>/var/lib/irods/msiExecCmd_bin</code>, which are executable, and are owned by IRODS.
  * Those scripts are available in the EuPathDBIrods project.
  * Copy over those scripts and if not already, make them excutable.  Make them owned by irods as well.
  ```bash
sudo cp /vagrant/scratch/project_home/EuPathDBIrods/Scripts/remoteExec/*.py /var/lib/irods/msiExecCmd_bin/.
sudo chmod 755 /var/lib/irods/msiExecCmd_bin/*.py
sudo chown irods.irods /var/lib/irods/msiExecCmd_bin/*.py
```

### Run the IRODS Builder Job
  * This job is parameterized with the username and password/token of the Jenkins user that will be calling the IRODS listener job from within the IRODS ecosystem.  Note that the password is actually hardcoded for now - that should change to this parametric input.
  * A third parameter, MODE, defaults to Dev.  Put anything else in its place to force a clean and complete rebuild of the shared workspace.  Note that the clean removes everything in the workspace.  For a virgin build, leave MODE empty.
  * This job will check out from svn, the 18 projects needed for the other IRODS jobs.
  * Additionally, the job will use the template configuration files in the joeuser home to create model-config.xml and [project].gus.config files for every project supported (as determined by the projectList.txt file).
  * Finally, the job will create the jenkinsCommunicationConfig.txt. It is located in IRODS at <code>/ebrc/workspaces</code> and will be used by one of the python scripts mentioned above to communicate with the IRODS Listener (irods-listener) job on Jenkins.
  * It would be prudent to be sure that file was created and properly placed.
  * The workspace will be <code>/var/tmp/jenkins-irods</code>.
  
### Deploy the IRODS Rest API
  * This service is needed to allow the transfer of user datasets from galaxy.
  * The [war file for version 4.1.10](https://github.com/DICE-UNC/irods-rest/releases) is in the EuPathDBIrods project.
  * In the VM, go to the tomcat webapps directory and copy the irods rest api war file there.
  ```bash
cd /usr/local/apache-tomcat-6.0.43/webapps
sudo cp /vagrant/scratch/project_home/EuPathDBIrods/Resources/irods-rest.war .
```
  * Create a directory that will house the properties file and drop the irods rest properties file into this new directory.
```bash
 sudo mkdir /etc/irods-ext
 sudo cp /vagrant/scratch/project_home/EuPathDBIrods/Resources/irods-rest.properties /etc/irods-ext/.
```
  * In the tomcat server.xml file, change the port from 8080 to 8180 (<code>sudo vi /usr/local/apache-tomcat/conf/server.xml</code>)
```xml 
	  <Connector port="8180" protocol="HTTP/1.1" 
	                connectionTimeout="20000" 
	                redirectPort="8443" />
```
  * Start tomcat.
```bash
   sudo /usr/local/apache-tomcat/bin/startup.sh
```
  * Verify that the rest service is working.
```bash
   curl -u wrkspuser:passWORD localhost:8180/irods-rest/rest/server
```
  * Modify the Vagrantfile to allow port 8180 through the firewall:
```ruby
	  config.vm.provider "virtualbox" do |v|
	    v.memory = 2048
	  end
  
	  tomcat\_port = 8180
	  config.vm.network "forwarded\_port", guest: tomcat\_port, host: tomcat\_port

	  config.vm.network :private\_network, type: :dhcp
	  config.vm.synced_folder ".", "/vagrant", type: "nfs"
	  
    ...
 
	    config.vm.provision :puppet do |puppet|
	      puppet.environment = 'savm'
	      puppet.environment_path = 'puppet/environments'
	      puppet.manifests_path = 'puppet/environments/savm/manifests'
	      puppet.manifest_file = 'site.pp'
	      puppet.hiera_config_path = 'puppet/hiera.yaml'
	      #puppet.options = ['--debug --trace --verbose']
	    end
  
	    config.vm.provision 'shell',
	       inline: "firewall-cmd --permanent --add-rich-rule=\"rule port port=#{tomcat\_port} protocol='tcp' accept\""
  
	    if ( Vagrant.has_plugin?('landrush') and config.landrush.enabled)
	      config.vm.provision :shell, inline: '/sbin/iptables-restore < /root/landrush.iptables'
	    end

	  end
  ```
  * Exit the VM and reload (<code>vagrant reload</code>).
  * My experience is that this reload step is insufficient by itself.  I have to run the firewall-cmd inside vagrant and then reload
  ```bash
  firewall-cmd --permanent --add-rich-rule="rule port port=8180 protocol='tcp' accept"
  ```
  * Then do another <code>vagrant reload</code>.
  * Once the VM is again running, restart tomcat and insure that the irods rest service is visible externally (check <code>http://wij.vm:8180/irods-rest/rest/server</code> using the same credentials as earlier).

### Galaxy Setup
  * Galaxy is assumed to be on the host here, rather than on the VM
  * Galaxy may be obtained [here](https://galaxyproject.org/admin/get-galaxy/).  In theory, Galaxy is always backward compatible.  So the latest download should work (but I wouldn't count on it).
  * My installation is at <code>~/Tools/galaxy/galaxy.</code>
  * Under the config directory, should be a galaxy.ini.  Open that and uncomment and change the port to 9090.
  * Also install planemo.  The installation instructions are on the [github page](https://github.com/galaxyproject/planemo).
  * Planemo will provide a Galaxy platform on which to test tools.

## End to End Testing
  Assuming a fresh laptop restart for the following testing.

### Insure Database Access
  * Insure that the host laptop and the vagrant box will have database access by running sshuttle on the laptop.
  ```bash
sshuttle -e 'ssh -o StrictHostKeyChecking=no' -r crisl@ash.pcbi.upenn.edu 128.91.49.128/24 128.192.0.0/16
```
  * On the VM, we can check that the databases are coming through the firewall by issuing tnsping for a database to be used.

### Setup and Start Vagrant
  * Start up the vagrant box (this in my directory structure - substitute your own).
```bash
    cd ~/Tools/vagrant-wij42
    vagrant up
```
  * Usually it is a good idea to <code>ping wij.vm</code> first as the network can sometimes go awry.  See Mark's notes for correcting that issue should it arise.
  * Also verify that Jenkins is running by visiting the url, <code>http://wij.vm:9171</code>

### Start IRODS Rest Service
  * Log into vagrant and turn on the tomcat instance supporting the irods rest service
```bash
vagrant ssh
sudo /usr/local/apache-tomcat/bin/startup.sh
```
  * A successful startup can be verified in the browser by visiting the url, <code>http://wij.vm:8180/irods-rest/rest/server</code>.  You will need to supply the IRODS user credentials.

### Setup and Start Website
  * A full end to end test requires one to examine the results in a project website.  I have one (for PlasmoDB) established on my laptop using [Ryan Doherty's setup instructions](http://conical.org/work/runningSiteLocally.html)
  * Start up the website.  Note that the configuration for this website includes a user dataset specification that points to the IRODS on wij.vm.  The following must be at the end of the yaml file used to generate the configuration file for this project.
  ```xml
   userDatasetStoreConfig: >
  <userDatasetStore implementation="org.gusdb.wdk.model.user.dataset.irods.IrodsUserDatasetStore">
   <property name="login">wrkspuser</property>
   <property name="password">passWORD</property>
   <property name="host">wij.vm</property>
   <property name="port">1247</property>
   <property name="resource">ebrcResc</property>
   <property name="zone">ebrc</property>
   <property name="rootPath">/ebrc/workspaces/users</property>
   <typeHandler type="example" version="1.0" implementation="org.gusdb.wdk.model.user.dataset.ExampleTypeHandler"/>
   <typeHandler type="GeneList" version="1.0"  implementation="org.apidb.apicommon.model.userdataset.GeneListTypeHandler"/>
  </userDatasetStore>
  ```
  * Remember to bring up vagrant and insure that the wij.vm host is accessible.  Otherwise, the website will fail to start when launched.
  * Make sure the site is up and login.

### Setup and Start Galaxy
  * On the laptop, go to the directory where the preliminary galaxy tools are located
  ```bash
cd ~/Tools/vagrant-wij42/scratch/project_home/EuPathDBIrods/Scripts/galaxyTools
```
  * To make the galaxy tool work, we need a configuration file named config.json that provides the connection information and credentials for connection to the IRODS rest service it is as follows for this instance:
  ```json
{
  "url": "http://wij.vm:8180/irods-rest/rest/fileContents/ebrc/workspaces/",
  "user": "wrkspuser",
  "password": "passWORD"
}
  ```
  * This file should be place in this galaxyTools directory.
  * Because this galaxy setup does not handle logging in using WDK user ids, I need to hardcode my WDK user id.  You can put your user id in place of mine in exportGeneListTOEuPathDB.py:
  ```python
    # Salt away all parameters.
    dataset_name = args[0]
    summary = args[1]
    description = args[2]
    dataset_file_path = args[3]
    #user_id = args[4]
    # My WDK user id for now
    user_id = "<put your id here>"
  ```
  * Now start galaxy:
  ```bash
  planemo s --galaxy_root ~/Tools/galaxy/galaxy
  ```
  * The site should be available in the browser at <code>localhost:9090</code>.

### Visit the User Datasets Workspace page
  * The GUI is not completely build out, but it is sufficient for testing.
  * Be sure to be logged in and visit the [website url for user datasets workspace](http://localhost:8080/plasmodb/app/workspace/datasets). Note that there is no link yet available on the site), 
  * If no datasets are available, an empty table should appear.

### Transfer a Dataset from Galaxy
  * Visit the galaxy website at <code>localhost:9090</code>.
  * Click on <code>Upload File from your computer</code> in the left hand menu.  In the dialog that opens, click on <code>Choose local file</code> and browse to <code>~/Tools/vagrant-wij42/scratch/project_home/EuPathDBIrods/Scripts/galaxyTools/test-data</code> and select <code>genelist.txt</code>.  Then click on <code>Start</code>.  Once loaded, click on <code>Close</code>.
  * This file contains a measly three genes, but it is adequate for proof of principle. Very large gene lists (> 10k) have worked but transfer is very lengthy with this environment.
  * In the left hand menu, click on the <code>Gene List to EuPathDB</code> link.
  * A dialog will open for the tool.  Fill out a name (alphanumerics only), a summary and a description.  All are required.
  * For the <code>Gene list to export</code> input, select the <code>genelist.txt</code> loaded earlier.
  * Click <code>Execute</code>.
  * The job will appear in the right hand frame and will hopefully transition from blue to yellow to green, indicating a successful transfer.

### Assess Results
  * If the browser page showing Jenkins has auto refresh enabled, the listener and the two (as is the case here) projects (Plasmo, Toxo) should indicate recent successful builds.  Otherwise, refresh the page.
  * Visit the user dataset page in the website and refresh if necessary.  The table should have the new dataset and the entry should indicate that the dataset is installed.
  * Click on the dataset id to visit the dataset page.  A link there, <code>My Gene List Dataset</code> should be available.  Click on that.
  * The page <code>Identify Gene based on My Gene List Dataset</code> should appear.  Select your dataset from the droplist and click <code>Get Answer</code>
  * A customary WDK summary page should appear showing the three genes (2 transcripts per gene).

# Additional Functional Tests
Since the website GUI is limited currently, further testing requires a REST client.  A useful one is [Postman](https://www.getpostman.com/).  That is what I used here.

### Deletion
  * Install a couple of datasets via Galaxy as described in end to end testing.
  * Identify one of those datasets via its ID (first column in the website's datasets table).
  * In Postman specify the method as <code>DELETE</code> and add the url, http://localhost:8080/plasmodb/service/user/108976930/user-dataset/<dataset id> with the id of the dataset to delete.
  * Click <code>Send</code>.  A successful response will be a 204 (No Content).  Check the website (refresh) to see that the dataset is gone and check Jenkins to insure that the events sent by IRODS were successfully handled.

### Sharing
  * For this, you will need another user's WDK id and another browser.
  * Create a json snippet to share one of the existing, previously unshared datasets like so:
```json
{
  "add": {
    "<dataset id>":["<user id>"]
  }
}
```
 * In a new Postman request, set the method to <code>PATCH</code> and add the url, localhost:8080/plasmodb/service/user/108976930/user-dataset/share
 * Add the json snippet to the body of the request and insure that the media type is application/json.
 * Click <code>Send</code>.  A successful response will be a 204 (No Content).  Check the webste (refresh) to see that the dataset has been shared ('Yes' under 'Shared With Others').
 * Visit the same website with a different browser, have the other user login and go to be user datasets page.  That user should now have access to that shared dataset.  Insure that the dataset is installed.
 

# How to Develop in this Env

Note that these modifications assume that the setup described in How to Set Up a Full IRODS Env for WDK on Vagrant is complete and correct.  These changes are not appropriate for production release.  Be careful - it is easy to inadvertantly run Unix commands rather than iCommands.

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
	  
  
  
  
  
  

  
  