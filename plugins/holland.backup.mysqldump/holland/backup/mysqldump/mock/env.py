from mocker import Mocker, ANY, CONTAINS, ARGS, KWARGS, MATCH
import storage
from _subprocess import PopenMock

class MockEnvironment(object):
    def __init__(self):
        self.mocker = Mocker()
        _setup_fileio(self.mocker)
        _setup_mysqlclient(self.mocker)
        _setup_subprocess(self.mocker)

    def replace_environment(self):
        self.mocker.replay()

    def restore_environment(self):
        # restore MySQLClient
        # restore normal file io
        # restore normal subprocess
        self.mocker.restore()

def _setup_fileio(mocker):
    """Patch __builtin__.open.

    Allow read access normally, but all writes go
    through the storage mock layer.
    """
    _open = mocker.replace('__builtin__.open')
    fileobj = _open(ANY, CONTAINS('w'), ANY)
    mocker.count(min=0,max=None)
    mocker.call(storage.open)

    fileobj = _open(ANY, CONTAINS('w'))
    mocker.count(min=0,max=None)
    mocker.call(storage.open)

    _mkdir = mocker.replace('os.mkdir')
    _mkdir(ARGS)
    mocker.count(min=0,max=None)

def _setup_mysqlclient(mocker):
    """Patch any dangerous methods on MySQLClient

    Used for dry-run support.  Currently avoid
    doing stop_slave or start_slave in dry-run mode
    but allow all other (read) operations.
    """
    client_cls = mocker.replace("holland.lib.mysql.client.AutoMySQLClient")
    client = client_cls(ARGS, KWARGS)

    client.connect()
    mocker.count(min=0,max=None)
    client.disconnect()
    mocker.count(min=0,max=None)
    # replace stop_slave, start_slave
    client.stop_slave()
    mocker.count(min=0,max=None)
    client.start_slave()
    mocker.count(min=0,max=None)

def match_mysqldump(param):
    if isinstance(param, list) and len(param) == 2:
        return param[0].endswith('mysqldump') and param[1] == '--version'
    return False

def _setup_subprocess(mocker):
    """Patch subprocess.Popen with a Mock object.

    In dry-run mode, don't run any commands - just
    fake it.
    """
    popen = mocker.replace("subprocess.Popen")
    pid = popen(MATCH(match_mysqldump), KWARGS)
    mocker.count(min=0,max=None)
    mocker.passthrough()

    pid = popen(ARGS, KWARGS)
    mocker.count(min=0,max=None)
    mocker.call(PopenMock)
