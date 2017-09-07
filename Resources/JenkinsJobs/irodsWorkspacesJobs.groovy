def node = 'irods'
def workspace = '/var/tmp/jenkins-irods'
def projects = ['PlasmoDB', 'ToxoDB']
def remoteJobToken = 'eupathdbirods'
def builderJob = 'irods-builder'
def listenerJob = 'irods-listener'
def handlerJobPrefix = 'irods-handler-'
def datasetStoreId = "DATASET_STORE_ID"
def emailRecipient = 'criswlawrence@gmail.com'
def sender = 'crisl@upenn.edu'

def handlerJobDesc = { project ->
  return """
    handler job for ${project} 
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
    
    # Unless this build is run in development mode, completely remove
    # everything in this workspace.  Then add back projectList.txt
     if [[ "\$MODE" != "Dev" ]]
      then
        rm -rf \$BASE_GUS/*
        cp /usr/local/home/joeuser/irods/projectList.txt "\$BASE_GUS/."
        cp /usr/local/home/joeuser/irods/site_vars.yml "\$BASE_GUS/."
    fi
    """.stripIndent()
}

def builderPostScmStep = {
  return """
    # Setup env variables for this build step
    export BASE_GUS="\$WORKSPACE"
    export GUS_HOME="\$BASE_GUS/gus_home"
    export PROJECT_HOME="\$BASE_GUS/project_home"
    export PATH="\$GUS_HOME/bin:\$PROJECT_HOME/install/bin:\$PATH"
    export PERL5LIB="\$GUS_HOME/lib/perl"
    export SITE_VARS="site_vars.yml"
    
    mkdir -p "\$GUS_HOME/lib/java/db_driver";
    
    cp "\$ORACLE_HOME/jdbc/lib/ojdbc6.jar" "\$GUS_HOME/lib/java/db_driver/"
    
    # do initial conifer install
    \$BASE_GUS/project_home/FgpUtil/Util/bin/conifer install \\
    --project-home \$BASE_GUS/project_home \\
    --gus-home \$BASE_GUS/gus_home \\
    --project PlasmoDB \\
    --cohort EuPathDBIrods \\
    --site-vars \$SITE_VARS \\
    --webapp-ctx none
    
    
    # configure each project listed in projectList.txt
    
    PROJECTS="\$(grep -v ^project projectList.txt | cut -f 1)"
    echo projects are: \$PROJECTS
    
    for PROJECT in \$PROJECTS
    do
      echo project is: \$PROJECT
      \$BASE_GUS/project_home/FgpUtil/Util/bin/conifer configure \\
      --project-home \$PROJECT_HOME \\
      --gus-home \$GUS_HOME \\
      --project \$PROJECT \\
      --cohort EuPathDBIrods \\
      --site-vars \$SITE_VARS \\
      --webapp-ctx none
      
    done
    
    # Contains all the project dependencies
    bld EuPathDBIrods

  """.stripIndent()
}

job('irods-builder') {
  description('')
  blockOn('^' + handlerJobPrefix + '.*')
  label(node)
  customWorkspace(workspace)
  parameters {
    stringParam('MODE', 'Dev', 'Indicates whether the mode of operation is development (DEV) or other.  If not development, a complete cleaning is done.')
  }
  scm {
    svn {
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/install/trunk') {
        directory('project_home/install')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/WSF/trunk') {
        directory('project_home/WSF')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/TuningManager/trunk') {
        directory('project_home/TuningManager')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/WDK/trunk') {
        directory('project_home/WDK')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/GusAppFramework/trunk') {
        directory('project_home/GUS')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/CBIL/trunk') {
        directory('project_home/CBIL')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/ReFlow/trunk') {
        directory('project_home/ReFlow')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/GusSchema/trunk') {
        directory('project_home/GusSchema')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/gus/FgpUtil/trunk') {
        directory('project_home/FgpUtil')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/ApiCommonData/trunk') {
        directory('project_home/ApiCommonData')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/EbrcWebsiteCommon/trunk') {
        directory('project_home/EbrcWebsiteCommon')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/DoTS/trunk') {
        directory('project_home/DoTS')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/ApiCommonWebService/trunk') {
        directory('project_home/ApiCommonWebService')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/ApiCommonWebsite/trunk') {
        directory('project_home/ApiCommonWebsite')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/EbrcWebSvcCommon/trunk') {
        directory('project_home/EbrcWebSvcCommon')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/ApiCommonModel/trunk') {
        directory('project_home/ApiCommonModel')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/EbrcModelCommon/trunk') {
        directory('project_home/EbrcModelCommon')
      }
      location('https://cbilsvn.pmacs.upenn.edu/svn/apidb/EuPathDBIrods/trunk') {
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
  publishers {
	extendedEmail {
	  recipientList(emailRecipient)
	  defaultSubject('Jenkins Message for the iRODS builder')
      defaultContent('EOM')
	  replyToList(sender)
	  triggers {
	    failure {
	      subject('Jenkins Failure for the iRODS builder')
	      content('Builder Failed')
		  attachBuildLog(true)
		  replyToList(sender)
		  recipientList(emailRecipient)
	    }
	  }
	}
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
  publishers {
	extendedEmail {
	  recipientList(emailRecipient)
	  defaultSubject('Jenkins Message for the iRODS listener')
      defaultContent('EOM')
	  replyToList(sender)
	  triggers {
	    failure {
	      subject('Jenkins Failure for the iRODS listener')
	      content('Listener failed')
		  attachBuildLog(true)
		  replyToList(sender)
		  recipientList(emailRecipient)
	    }
	  }
	}
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
	publishers {
	  extendedEmail {
	    recipientList(emailRecipient)
	    defaultSubject('Jenkins Message for the ' + project + ' iRODS handler')
		defaultContent('EOM')
		replyToList(sender)
	    triggers {
	      failure {
	        subject('Jenkins Failure for the ' + project + ' iRODS handler')
	        content('Handler failed')
			attachBuildLog(true)
			replyToList(sender)
			recipientList(emailRecipient)
	      }
	    }
	  }
	}
  }
}
