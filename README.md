# EuPathDBIrods
Software to install in VEuPathDB's [iRODS](https://irods.org/) server.  iRODS supports code plugins written in python and in the [iRODS Rule Language](https://docs.irods.org/4.1.5/manual/rule_language/), both of which are used here.

The software [plugged into iRODS](https://docs.irods.org/4.2.2/system_overview/configuration/) is in support of the VEuPathDB User Datasets system.  User data sets uploaded to VEuPathDB are stored in iRODS, for future controlled access by the user (and others that are granted share access).  The iRODS plugins implement a workflow that includes unpacking user files, storing them in the proper location for that user, and emitting an event so that subscribers (eg, a VEuPathDB website) can display updated User Dataset information.


