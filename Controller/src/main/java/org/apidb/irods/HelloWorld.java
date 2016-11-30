package org.apidb.irods;

/**
 * Simple test of remote script call from IRODS via Jenkins.
 * HelloWorld.class located in /var/lib/jenkins/workspaces/HelloWorld/org/apidb/irods
 * Jenkins build script is java org/apidb/irods/HelloWorld
 * Remote call url is http://ies.irods.vm:8080/job/HelloWorld/build?token=helloworldtest
 * Url located in jobFile.txt
 * @author crisl-adm
 *
 */
public class HelloWorld {
  public static void main(String[] args) {
	System.out.println("Hello World");
  }
}
