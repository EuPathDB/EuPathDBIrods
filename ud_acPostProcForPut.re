# Custom event hook for user dataset post processiong following an iput
acPostProcForPut {
	msiSplitPath($objPath, *fileDir, *fileName);
	# if a tgz file is put into the landing zone, unpack it
	if(*fileDir == "/ebrc/workspaces/lz" && *fileName like "*.tgz") then {
		acLandingZonePostProcForPut(*fileDir, *fileName);
	}
}


