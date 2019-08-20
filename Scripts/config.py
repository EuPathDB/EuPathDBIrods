class Config:
    IRODS_ID = "irods_id"

    DATASET_CONFIG_FILE = "dataset.json"
    DATASET_META_FILE = "meta.json"

    class Paths:
        HOME = "/ebrc/workspaces"
        STAGING = HOME + "/staging"
        EVENTS = HOME + "/events"
        LZ = HOME + "/lz"
        FLAGS = HOME + "/flags"
        USERS = HOME + "/users"
        DEFAULT_QUOTA = USERS + "/default_quota"

        def __init__(self):
            pass

    class Debug:
        """
        Debugging options
        """
        # Enable trace level logging
        ENABLE_TRACE = False

    def __init__(self):
        pass

    @staticmethod
    def as_irods_string(irods):
        return irods.encode_key_val({
            "irodsId":           Config.IRODS_ID,
            "datasetConfigFile": Config.DATASET_CONFIG_FILE,
            "datasetMetaFile":   Config.DATASET_META_FILE,
            "homePath":          Config.Paths.HOME,
            "stagingAreaPath":   Config.Paths.STAGING,
            "eventsPath":        Config.Paths.EVENTS,
            "flagsPath":         Config.Paths.FLAGS,
            "landingZonePath":   Config.Paths.LZ,
            "usersPath":         Config.Paths.USERS,
            "defaultQuotaPath":  Config.Paths.DEFAULT_QUOTA,
        })
