package org.apidb.irods;

/**
 * Simple test of remote script call from IRODS via Jenkins.
 * SanityTest.class located in /var/lib/jenkins/workspaces/SanityTest/org/apidb/irods
 * Jenkins build script is java org/apidb/irods/SanityTest
 * Remote call url is http://ies.irods.vm:8080/job/SanityTest/build?token=sanitytest
 * Url located in jobFile.txt
 * @author crisl-adm
 *
 */
public class SanityTest {
  
  public static void main(String[] args) {
	System.out.println("Sanity Test");
  }
	
}
