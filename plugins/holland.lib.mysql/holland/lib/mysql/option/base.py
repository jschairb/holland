"""MySQL option files support

http://dev.mysql.com/doc/refman/5.1/en/option-files.html
"""
import os, sys
import re
import codecs
import logging
from holland.core.config import ConfigObj, ConfigObjError, ParseError

LOG = logging.getLogger(__name__)

def merge_options(path,
                  *defaults_files,
                  **kwargs):
    defaults_config = ConfigObj(list_values=False)
    defaults_config['client'] = {}
    for config in defaults_files:
        _my_config = load_options(config)
        defaults_config.update(_my_config)

    for key in ('user', 'password', 'socket', 'host', 'port'):
        if kwargs.get(key) is not None:
            defaults_config['client'][key] = kwargs[key]
    write_options(defaults_config, path)

def load_options(path):
    """Load mysql option file from filename"""
    path = os.path.abspath(os.path.expanduser(path))
    cfg = ConfigObj(list_values=False)
    cfg.filename = path
    try:
        cfg.reload()
    except ConfigObjError, exc:
        LOG.debug("Skipping unparsable lines")
        for _exc in exc.errors:
            LOG.debug("Ignored line %d: %s", _exc.lineno, _exc.line.rstrip())
    return client_sections(cfg)

def unquote(value):
    """Remove quotes from a string."""
    if len(value) > 1 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]

    # substitute meta characters per:
    # http://dev.mysql.com/doc/refman/5.0/en/option-files.html
    MYSQL_META = {
        'b' : "\b",
        't' : "\t",
        'n' : "\n",
        'r' : "\r",
        '\\': "\\",
        's' : " ",
        '"' : '"',
    }
    return re.sub(r'\\(["btnr\\s])',
                  lambda m: MYSQL_META[m.group(1)],
                  value)

def quote(value):
    """Added quotes around a value"""

    return '"' + value.replace('"', '\\"') + '"'

def client_sections(config):
    """Create a copy of config with only valid client auth sections

    This includes [client], [mysql] and [mysqldump] with only options
    related to mysql authentication.
    """

    clean_cfg = ConfigObj(list_values=False)
    clean_cfg['client'] = {}
    valid_sections = ['client', 'mysql', 'holland']
    for section in valid_sections:
        if section in config:
            clean_section = client_keys(config[section])
            clean_cfg['client'].update(clean_section)
    return clean_cfg

def client_keys(config):
    """Create a copy of option_section with non-authentication options
    stripped out.

    Authentication options supported are:
    user, password, host, port, and socket
    """
    clean_namespace = ConfigObj(list_values=False)
    clean_namespace.update(config)
    valid_keys = ['user', 'password', 'host', 'port', 'socket']
    for key in config:
        if key not in valid_keys:
            del clean_namespace[key]
        else:
            clean_namespace[key] = unquote(config[key])
    return clean_namespace

def write_options(config, filename):
    quoted_config = ConfigObj(list_values=False)
    quoted_config.update(config)

    if isinstance(filename, basestring):
        filename = codecs.open(filename, 'w', 'utf8')
    quoted_config.write(filename)
    filename.close()

def build_mysql_config(mysql_config):
    """Given a standard Holland [mysql:client] section build an in-memory
    config that represents the auth parameters, including those merged in from
    *defaults-extra-files*

    :param mysql_config: required.  This should be a dict object with the
                         zero or more of the following keys:
                           user (string)
                           password (string)
                           host (string)
                           socket (string)
                           port (integer)
                           defaults-extra-file (list)
    :type mysql_config: dict
    """
    defaults_config = ConfigObj()
    defaults_config['client'] = {}
    for config in mysql_config['defaults-extra-file']:
        LOG.info("Loading %s [%s]", config, os.path.expanduser(config))
        _my_config = load_options(config)
        defaults_config.update(_my_config)

    for key in ('user', 'password', 'socket', 'host', 'port'):
        if key in mysql_config and mysql_config[key]:
            defaults_config['client'][key] = mysql_config[key]
    return defaults_config
