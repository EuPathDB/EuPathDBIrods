import irods_types
import debug


#
# Enums
#


class OpenFlag:
    READ_ONLY = 'O_RDONLY'


class ObjectType:
    COLLECTION = "-C"
    DATA_OBJECT = "-d"
    RESOURCE = "-R"
    RESOURCE_GROUP = "-G"
    USER = "-u"


#
# Implementations
#

class Irods(object):
    """
    Irods Internals Wrapper

    Intended to provide a barrier between our code and the convoluted irods code.
    """
    def __init__(self, irods):
        # iRODS Callback Container
        self._irods = irods

        # Enable method tracing
        self._trace = True

    #
    # iRODS Microservice Wrapper Methods
    #

    def str_to_key_value(self, pair):
        """
        Wrapper for msiString2KeyValuePair.

        :param str pair: stringified key value pair
        :rtype: irods_types.KeyValPair
        """
        debug.trace_begin(self, locals())
        return self.validate_result(self._irods.msiString2KeyValPair(pair, irods_types.KeyValPair()), 1)

    def add_key_val(self, key, val, key_vals=None):
        """
        Wrapper for msiAddKeyVal.  Appends the given key value pair to the optional input key_vals param.  If the
        key_vals param is None, a new KeyValPair will be created.

        :param str key: meta attribute key
        :param str val: meta attribute value
        :param irods_types.KeyValPair key_vals:
        :return: the updated KeyValPair
        :rtype: irods_types.KeyValPair
        """
        debug.trace_begin(self, locals())
        check_kvp_key(key)

        if key_vals is None:
            key_vals = irods_types.KeyValPair()

        return self.validate_result(self._irods.msiAddKeyVal(key_vals, key, val if val is not None else ""), 0)

    def associate_key_value_pairs_to_obj(self, kvp, path, flag):
        """
        Wrapper for msiAssociateKeyValuePairsToObj.  Takes the given key value pairs object and associates it with the
        given path in the KVU store.

        :param irods_types.KeyValPair kvp: set of key value pairs to associate with the given path
        :param str path: path to which the given key value pairs will be associated
        :param str flag: object type that the given path points to
        """
        debug.trace_begin(self, locals())
        self.validate_result(self._irods.msiAssociateKeyValuePairsToObj(kvp, path, flag))

    def remove_key_value_pairs_from_obj(self, kvp, path, flag):
        """
        Wrapper for msiRemoveKeyValuePairsFromObj.  Removes all key value pairs that match entries in the input key
        value pairs from the given path.

        :param irods_types.KeyValPair kvp: key value pairs to remove from the path
        :param str path: path from which the key value pairs should be removed
        :param str flag: object type that the given path points to
        """
        debug.trace_begin(self, locals())
        self.validate_result(self._irods.msiRemoveKeyValuePairsFromObj(kvp, path, flag))

    def data_obj_open(self, path, flag=None):
        """
        Wrapper for msiDataObjOpen.  Takes the given input path, and optional open flag and returns a handle to the file
        at the given path.

        :param str path: path to the file to open
        :param str flag: open flag
        :return: file handle
        :rtype: int
        """
        debug.trace_begin(self, locals())
        con = "objPath={}".format(path) if flag is None else "objPath={}++++openFlags={}".format(path, flag)
        return debug.trace_end(self, self.validate_result(self._irods.msiDataObjOpen(con, 0), 1))

    def data_obj_read(self, handle, length):
        """
        Wrapper for msiDataObjRead.  Takes the given input file handle and length and reads `length` bytes from the open
        file.

        :param int handle: open file handle
        :param int length: number of bytes to read
        :rtype: irods_types.BytesBuf
        :returns: buffer containing the read bytes
        """
        debug.trace_begin(self, locals())
        return debug.trace_end(self, self.validate_result(self._irods.msiDataObjRead(handle, length, 0), 2))

    def data_obj_close(self, handle):
        """
        Wrapper for msiDataObjClose.  Takes the given input file handle and attempts to close the open file.

        :param int handle: handle to the open file to close
        """
        debug.trace_begin(self, locals())
        self.validate_result(self._irods.msiDataObjClose(handle, 0))
        debug.trace_end(self)

    def obj_stat(self, path):
        """
        Wrapper for msiObjStat.  Returns file system stat info about the data object at the given path.

        :param str path: path to the file to stat
        :rtype: irods_types.RodsObjStat
        """
        debug.trace_begin(self, locals())
        return debug.trace_end(self, self.validate_result(self._irods.msiObjStat(path, 0), 1))

    def make_gen_query(self, cols, filters):
        """
        Wrapper for msiMakeGenQuery.  Creates an iRODS gen query from the given input select columns and filters.

        :param list[str] cols: columns to select
        :param list[str] filters: preconstructed individual predicates (Ex: "DATA_NAME = 'foo'")
        :return: a constructed GenQueryInp instance
        :rtype: irods_types.GenQueryInp
        """
        debug.trace_begin(self, locals())
        return debug.trace_end(self, self.validate_result(self._irods.msiMakeGenQuery(
            ", ".join(cols), " AND ".join(filters), irods_types.GenQueryInp()), 2))

    def exec_gen_query(self, query):
        """
        Wrapper for msiExecGenQuery.  Executes a given GenQueryInp query (constructed with make_gen_query).

        :param irods_types.GenQueryInp query: preprocessed iRODS gen query to execute
        :return: the result of the query execution
        :rtype: irods_types.GenQueryOut
        """
        debug.trace_begin(self, locals())
        return debug.trace_end(self, self.validate_result(
            self._irods.msiExecGenQuery(query, irods_types.GenQueryOut()), 1))

    def get_cont_inx_from_gen_query_out(self, result):
        """
        Wrapper for msiGetContInxFromGenQueryOut.  Returns the continuation index for the given query result.  A value
        greater than 0 indicates additional rows are available

        :param irods_types.GenQueryOut result: gen query result
        :return: the continuation index.  A value > 0 means there are more rows available
        :rtype: int
        """
        debug.trace_begin(self, locals())
        return debug.trace_end(self, self.validate_result(self._irods.msiGetContInxFromGenQueryOut(result, 0), 1))

    def get_more_rows(self, query):
        """
        Wrapper for msiGetMoreRows.  Reruns the given query at the continuation index to retrieve additional rows.

        :param query:
        :returns: a tuple of the query result, and the new continuation index.
        :rtype: (irods_types.GenQueryOut, int)
        """
        debug.trace_begin(self, locals())
        res = self._irods.msiGetMoreRows(query, irods_types.GenQueryOut(), 0)
        return debug.trace_end(self, (self.validate_result(res, 1), self.validate_result(res, 2)))

    #
    # Custom Methods
    #

    def write_line_raw(self, target, message):
        self._irods.writeLine(target, message)

    def write_log(self, message):
        self.write_line_raw("serverLog", "Py: " + str(message))

    def validate_result(self, res, index=None):
        debug.trace_begin(self, locals())
        if res['status'] and res['code'] >= 0:
            return debug.trace_end(self, res['arguments'][index] if index is not None else None)
        raise IrodsError(res['status'])

    def read_obj_contents(self, path):
        """
        Read the contents of the data object at the given path as a string.

        :param str path: path to the data object to read
        :param Irods irods: irods wrapper
        :rtype: str
        :returns: contents of the data object at the given path
        """
        debug.trace_begin(self, locals())
        size = self.obj_stat(path).objSize
        fd = self.data_obj_open(path, OpenFlag.READ_ONLY)
        res = self.data_obj_read(fd, size)
        self.data_obj_close(fd)
        out = str(res.buf[:size])
        return debug.trace_end(self, out[:size])

    def run_gen_query(self, cols, filters):
        """
        Wrapper for a full query run including make_gen_query, exec_gen_query, get_cont_inx_from_gen_query_out, and
        get_more_rows.

        Builds and runs a query based on the input columns and filters and returns the results as a list of dicts
        containing the column name as a key, and the column value as a string value.

        :param list[str] cols: a list of valid iCAT column names to select
        :param list[str] filters: a list of predicates to apply to the results
            (EX: ["DATA_NAME = 'foo'","COLL_NAME = 'bar'])
        :return: a list of dicts representing result rows containing the select column name mapped to that columns value
        :rtype: list[dict]
        """
        debug.trace_begin(self, locals())
        query = self.make_gen_query(cols, filters)
        result = self.exec_gen_query(query)
        out = []

        while True:
            cont_ind = self.get_cont_inx_from_gen_query_out(result)

            for j in xrange(result.rowCnt):
                row = [result.sqlResult[i].row(j) for i in xrange(len(cols))]
                out.append(dict(zip(cols, row)))

            if cont_ind > 0:
                result, cont_ind = self.get_more_rows(query)
            else:
                break

        return debug.trace_end(self, out)

    def encode_key_val(self, kvp):
        """
        String encodes the given key value pair object into a format safe for use with msiString2KeyValPair

        :param irods_types.KeyValPair|dict kvp:
        :return: iRODS style string encoding of the given key value pair object
        :rtype: string
        """
        debug.trace_begin(self, locals())
        return debug.trace_end(self, '%'.join([
            check_kvp_key(kvp_escape_string(k)) + '=' + kvp_escape_string(v)
            for (k, v) in (kvp_iter(kvp) if isinstance(kvp, irods_types.KeyValPair) else kvp.iteritems())
        ]))

    def key_val_to_dict(self, kvp):
        """
        Converts an iRODS KeyValPair to a python dict.

        :param irods_types.KeyValPair kvp:
        :return: dictionary of key: list(val)
        :rtype: dict
        """
        debug.trace_begin(self, locals())
        out = {}
        for k, v in kvp_iter(kvp):
            if k in out:
                out[k].append(v)
            else:
                out[k] = [v]
        return debug.trace_end(self, out)

    def make_key_vals(self, kvals):
        """
        Creates an iRODS KeyValuePair struct out of the given kvals dict.

        :param dict kvals: key value pairs to be inserted into the new KeyValPair struct.
        :rtype: irods_types.KeyValPair
        :returns: an iRODS KeyValuePair type containing the given input key value pairs
        """
        debug.trace_begin(self, locals())
        obj = irods_types.KeyValPair()
        for key, val in kvals.iteritems():
            obj = self.add_key_val(key, val, obj)
        return obj


class IrodsError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def kvp_iter(kvp):
    for i in xrange(kvp.len):
        yield str(kvp.key[i]), str(kvp.value[i])


def check_kvp_key(key):
    """
    Weird bug prevention:

    Since we are crossing the barrier between iRODS rule lang and python,
    we need to stringify key value pairs.  iRODS key value parsing will
    pick the first instance of '=' it sees as the divider between key and
    value which can result in undefined behavior.

    To prevent this, disallow '=' in keys altogether.

    :param str key:
    :returns: input string
    :rtype: str
    """
    if '=' in key:
        raise IrodsError("Illegal '=' character in key '{}'".format(key))
    return key


def kvp_escape_string(val):
    """
    Escapes the input string to be safe for use as a key or value.

    :param str val:
    :return: escaped string
    """
    return str(val).replace('%', '%%')
