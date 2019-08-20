import json
import os
from config import Config
from ebrc_irods import ObjectType, Irods


# ----------------------------------------------------------
#
# iRODS Methods
#
# ----------------------------------------------------------


def fill_literals(args, callback, rei):
    """
    iRODS Rule language calling point for retrieving the constants collection.

    :param list[str] args: should be called with exactly 1 string argument.
        Other arguments will be ignored
    :param any callback: iRODS rule language/microservice accessor
    :param any rei: iRODS rei
    """
    irods = Irods(callback)
    args[0] = Config.as_irods_string(irods)


def write_dataset_metadata(args, callback, rei):
    """
    Writes the contents of dataset.json and meta.json to a dataset's key/value store.

    :param list[str] args: args[0] should be the path to the newly created datasaet.
        All other args are ignored.
    :param any callback: iRODS rule language/microservice accessor
    :param any rei: iRODS rei
    """
    irods = Irods(callback)
    path = args[0]

    irods.write_log("Writing dataset.json & meta.json to metadata for path " + path)

    kvp = irods.make_key_vals({
        Config.DATASET_CONFIG_FILE: strip_data_files(
            irods.read_obj_contents(os.path.join(path, Config.DATASET_CONFIG_FILE))
        ),
        Config.DATASET_META_FILE: minify(irods.read_obj_contents(os.path.join(path, Config.DATASET_META_FILE)))
    })

    irods.associate_key_value_pairs_to_obj(kvp, path, ObjectType.COLLECTION)


# ----------------------------------------------------------
#
# Helpers and utilities
#
# ----------------------------------------------------------


def minify(js):
    """
    Minifies the input json string or object.

    :param object|str js: input json string or object (which will be stringified)
    :return: minified json string
    :rtype: str
    """
    return json.dumps(obj=json.loads(js) if type(js) == str else js, separators=(',', ':'))


def strip_data_files(config_str):
    """
    Removes the "dataFiles" element from the input json string and returns a minified updated json string.

    :param str config_str: json string
    :return: minified json string with the "dataFiles" element removed.
    :rtype: str
    """
    config_json = json.loads(config_str)
    del (config_json['dataFiles'])
    return minify(config_json)
