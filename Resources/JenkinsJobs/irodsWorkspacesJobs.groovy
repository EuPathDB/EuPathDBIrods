def node = 'irods'
def workspace = '/var/tmp/jenkins-irods'
def projects = ['PlasmoDB', 'ToxoDB']
def remoteJobToken = 'eupathdbirods'
def builderJob = 'irods-builder'
def listenerJob = 'irods-listener'
def handlerJobPrefix = 'irods-handler-'
def datasetStoreId = "DATASET_STORE_ID"

def handlerJobDesc = { project ->
  def thisBuild = Thread.currentThread().executable // a hudson.model.FreeStyleBuild
  def thisProject = thisBuild.project // a hudson.model.FreeStyleProject
  return """
    Listens to iRODS events for ${project}.
    <p>
    <font color='red'>This project configuration is auto-generated by
    <a href="/${thisProject.url}">${thisProject.displayName}</a>. <br>
    (Generated by <a href="/${thisBuild.url}">${thisBuild.displayName}<a/>)
  """.stripIndent()
}

def handlerStep = { project ->
  return """
    export BASE_GUS="\$WORKSPACE"
    export GUS_HOME="\$BASE_GUS/gus_home"
    export PROJECT_HOME="\$BASE_GUS/project_home"
    export PATH="\$GUS_HOME/bin:\$PROJECT_HOME/install/bin:\$PATH"
    export PERL5LIB="\$GUS_HOME/lib/perl"
	export PROJECT_ID="${project}"

    fgpJava org.apidb.irods.BuildEventsFile
  """.stripIndent()
}

def listenerStep = {
  return """
    jenkins.model.Jenkins.instance.items.each {
      if (it.name ==~ /^irods-handler-.*/) {
        println "Starting " + it.name
		def build = Thread.currentThread().executable
		def key = "${datasetStoreId}"
		def resolver = build.buildVariableResolver
		def value = resolver.resolve(key)
		def param = new hudson.model.StringParameterValue(key, value)
	    def paramAction = new hudson.model.ParametersAction(param)
        hudson.model.Hudson.instance.queue.schedule(it, 0, paramAction)
      }
    }
  """.stripIndent()
}

def builderPreScmStep = {
    return """
	# Setup env variables for this build step
	export BASE_GUS="\$WORKSPACE"
	export GUS_HOME="\$BASE_GUS/gus_home"
	export PROJECT_HOME="\$BASE_GUS/project_home"

	# Unless this build is run in development mode, completely remove
	# gus/project homes in this workspace.  Leaving the templates at
	# the top level of the worksapce intact for now.
	if [[ "\$MODE" != "Dev" ]]
	 then
	  if [ -d "\$PROJECT_HOME" ]
	   then
	    rm -rf "\$PROJECT_HOME"
	    echo "Removed project home."
	  fi  
	  if [ -d "\$GUS_HOME" ]
	   then
	    rm -rf "\$GUS_HOME"
	    echo "Removed gus home."
	  fi
	fi
    """.stripIndent()
}

def builderPostScmStep = {
  def thisBuild = Thread.currentThread().executable // a hudson.model.FreeStyleBuild
  def thisProjectUrl = thisBuild.project.url
  def listenerJobRemoteTriggerUrl = "${BUILD_URL}".substring(0, "${BUILD_URL}".lastIndexOf("job/")) + "job/" + listenerJob + "/buildWithParameters"
  return """
  # Setup env variables for this build step
  export BASE_GUS="\$WORKSPACE"
  export GUS_HOME="\$BASE_GUS/gus_home"
  export PROJECT_HOME="\$BASE_GUS/project_home"
  export PATH="\$GUS_HOME/bin:\$PROJECT_HOME/install/bin:\$PATH"
  export PERL5LIB="\$GUS_HOME/lib/perl"

  mkdir -p gus_home

  mkdir -p "\$GUS_HOME/lib/java/db_driver";

  cp "\$ORACLE_HOME/jdbc/lib/ojdbc6.jar" "\$GUS_HOME/lib/java/db_driver/"

  # ApiCommonData build, upon which EuPathDBIrods depends, requires this file.
  mkdir -p "\$GUS_HOME/config"
  cp "\$BASE_GUS/gus.config" "\$GUS_HOME/config/gus.config"

  # Contains all the project dependencies
  bld EuPathDBIrods

  # There will be multiple calls here - a different yaml for each project
  # Directory named after project made user \$GUS_HOME/config when eupathSiteConfigure is run.
  apiTnsSummary | grep -v amaz-rbld | grep -v pris-rbld | eupathCloneMetaFile "\$BASE_GUS/PlasmoDBMetaConfig.yaml"

  # By convention, all meta config yaml files have this file name suffix.  The prefix is the
  # project id.  Run eupathSiteConfigure for each project in the projectList.txt file.
  FILE_SUFFIX="MetaConfig.yaml"
  PROJECTS="\$(cat projectList.txt | cut -f 2)"
  PROJECT_ARRAY=(`echo "\$PROJECTS"`);
  for PROJECT in "\${PROJECT_ARRAY[@]}"
	do
	  eupathSiteConfigure -model "\$PROJECT" -filename "\$PROJECT\$FILE_SUFFIX"
	done


  # Needed for ApiCommonData build upon which EuPathDBIrods depends
  # Note that these steps follow the eupathSiteConfigure cmd because they require the dir
  # that eupathSiteConfigure creates.
  eupathCloneGusConfigFile gus.config -inc projectList.txt


  # This builds and places the jenkinsCommunicationConfig.txt file used by IRODS to call
  # Jenkins IRODS Listener job
  fgpJava org.apidb.irods.BuildJenkinsCommunicationFile -u "\$JENKINS_USERNAME" -p "be4797e4b88200492d29cf0aeb32f5de" -j ${listenerJobRemoteTriggerUrl} -t ${remoteJobToken} -l "\${PROJECT_ARRAY[0]}"
  """.stripIndent()
}

job('irods-builder') {
  description('')
  blockOn('^' + handlerJobPrefix + '.*')
  label(node)
  customWorkspace(workspace)
  parameters {
	stringParam('JENKINS_USERNAME', 'wrkspuser', 'This is the Jenkins user that is calling the IRODS Listener job')
	stringParam('JENKINS_USER_PASSWORD', '', 'The password/token belonging to the Jenkins user calling the IRODS Listener job')
    stringParam('MODE', 'Dev', 'Indicates whether the mode of operation is development (DEV) or other.  If not development, a complete cleaning is done.')
  }
  scm {
    svn {
      location('https://www.cbil.upenn.edu/svn/gus/install/trunk') {
        directory('project_home/install')
      }
      location('https://www.cbil.upenn.edu/svn/gus/WSF/trunk') {
        directory('project_home/WSF')
      }
      location('https://www.cbil.upenn.edu/svn/gus/TuningManager/trunk') {
        directory('project_home/TuningManager')
      }
      location('https://www.cbil.upenn.edu/svn/gus/WDK/trunk') {
        directory('project_home/WDK')
      }
      location('https://www.cbil.upenn.edu/svn/gus/GusAppFramework/trunk') {
        directory('project_home/GUS')
      }
      location('https://www.cbil.upenn.edu/svn/gus/CBIL/trunk') {
        directory('project_home/CBIL')
      }
      location('https://www.cbil.upenn.edu/svn/gus/ReFlow/trunk') {
        directory('project_home/ReFlow')
      }
      location('https://www.cbil.upenn.edu/svn/gus/GusSchema/trunk') {
        directory('project_home/GusSchema')
      }
      location('https://www.cbil.upenn.edu/svn/gus/FgpUtil/trunk') {
        directory('project_home/FgpUtil')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/ApiCommonData/trunk') {
        directory('project_home/ApiCommonData')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/EuPathSiteCommon/trunk') {
        directory('project_home/EuPathSiteCommon')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/DoTS/trunk') {
        directory('project_home/DoTS')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/ApiCommonWebService/trunk') {
        directory('project_home/ApiCommonWebService')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/ApiCommonWebsite/trunk') {
        directory('project_home/ApiCommonWebsite')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/EuPathWebSvcCommon/trunk') {
        directory('project_home/EuPathWebSvcCommon')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/ApiCommonShared/trunk') {
        directory('project_home/ApiCommonShared')
      }
      location('https://www.cbil.upenn.edu/svn/apidb/EuPathDBIrods/trunk') {
        directory('project_home/EuPathDBIrods')
      }
    }
  }
  triggers {
    scm('H H * * *')
  }
  wrappers {
    preScmSteps {
      steps {
        shell(builderPreScmStep())
      }
      failOnError()
    }
  }
  steps {
    shell(builderPostScmStep())
  }
}

job('irods-listener') {
  description('Trigger all irods-handler-.* jobs')
  parameters {
	stringParam(datasetStoreId, '', 'This is essentially the signature of the dataset store calling this listener.')
  }
  steps {
    systemGroovyCommand(listenerStep())
  }
}

for(project in projects) {
  jobName = handlerJobPrefix + project
  job(jobName) {
    description(handlerJobDesc(project))
    parameters {
  	  stringParam(datasetStoreId, '', 'This is essentially the signature of the dataset store calling this handler\'s listener.')
    }
    blockOn(builderJob)
    label(node)
    customWorkspace(workspace)
	authenticationToken(remoteJobToken)
    steps {
      shell(handlerStep(project))
    }
  }
}