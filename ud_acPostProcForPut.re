
acPostProcForPut {
	msiSplitPath($objPath, *fileDir, *fileName);
	if(*fileDir == "/ebrc/workspaces/lz") {
		acLandingZonePostProcForPut(*fileDir, *fileName);
	}
}


