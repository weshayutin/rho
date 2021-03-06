#
# Copyright (c) 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

""" Configuration Objects and Parsing Module """

import simplejson as json

# Keys used in the configuration JSON:
CREDENTIALS_KEY = "credentials"
GROUPS_KEY = "groups"
VERSION_KEY = "version"
NAME_KEY = "name"
TYPE_KEY = "type"
USERNAME_KEY = "username"
PASSWORD_KEY = "password"
SSHKEY_KEY = "key"
RANGE_KEY = "range"
PORTS_KEY = "ports"

SSH_TYPE = "ssh"
SSH_KEY_TYPE = "ssh_key"

# Current config version, bump this if we ever change the format:
CONFIG_VERSION = 1


class BadJsonException(Exception):
    pass


class ConfigError(Exception):
    pass


class DuplicateNameError(Exception):
    pass


def verify_keys(check_dict, required=[], optional=None):
    """
    Verify that all required keys are present in the dict, and nothing
    extraneous is present.

    Assumes that if optional arguments is not specified, we're only checking
    for required keys and can safely pass over anything extra. Specify an
    empty list for optional if you wish to check for required tags and
    error out if anything extra is found.

    Will throw a ConfigError if anything is amiss.
    """
    for required_key in required:
        if required_key not in check_dict:
            raise ConfigError("Missing required key: %s" % 
                    required_key)

    if optional is not None:
        for key in check_dict:
            if (key not in required) and (key not in optional):
                raise ConfigError("Extraneous key: %s" %
                        required_key)


class Config(object):
    """ Simple object represeting Rho configuration. """

    def __init__(self, credentials=None, groups=None):
        """
        Create a config object from the given credentials and groups.
        """

        self._credentials = []
        self._groups = []
        # Will map credential key name to the credentials object:
        self._credential_index = {}
        self._group_index = {}

        # Need to iterate credentials first:
        if credentials:
            for c in credentials:
                self.add_credentials(c)

        if groups:
            # Make sure none of the groups reference invalid credential keys:
            for group in groups:
                self.add_group(group)

    def add_credentials(self, c):

        if c.name in self._credential_index:
            raise DuplicateNameError

        self._credentials.append(c)
        self._credential_index[c.name] = c

    def remove_credential(self, cname):
        if self._credential_index.has_key(cname):
            c = self._credential_index[cname]
            self._credentials.remove(c)
            del self._credential_index[cname]
        # TODO: need to raise error here, user shouldn't see nothing if
        # they botched their command to remove a credential

    def get_credentials(self, cname):
        return self._credential_index.get(cname)

    def list_credentials(self):
        """ Return a list of all credential objects in this configuration. """
        # TODO: Should this return a copy of list? Immutable?
        return self._credentials

    def clear_credentials(self):
        self._credentials = []
        self._credential_index = {}

    def add_group(self, group):
        """ 
        Add a new group to this configuration, and ensure it references valid
        credentials.
        """
        if group.name in self._group_index:
            raise DuplicateNameError(group.name)

        for c in group.credential_names:
            if c not in self._credential_index:
                raise ConfigError("No such credentials: %s" %
                        c)

        self._groups.append(group)
        self._group_index[group.name] = group

    def list_groups(self):
        """ Return a list of all groups in this configuration. """
        return self._groups

    def get_group(self, gname):
        return self._group_index.get(gname)

    def clear_groups(self):
        self._groups = []
        self._group_index = {}

    def to_dict(self):
        creds = []
        for c in self._credentials:
            creds.append(c.to_dict())
        groups = []
        for g in self._groups:
            groups.append(g.to_dict())
        return {
                VERSION_KEY: CONFIG_VERSION,
                CREDENTIALS_KEY: creds,
                GROUPS_KEY: groups
        }


class Credentials(object):

    def to_dict(self):
        raise NotImplementedError


class SshCredentials(Credentials):

    def __init__(self, json_dict):

        verify_keys(json_dict, required=[NAME_KEY, TYPE_KEY,
                USERNAME_KEY, PASSWORD_KEY], optional=[])

        self.name = json_dict[NAME_KEY]
        self.username = json_dict[USERNAME_KEY]
        self.password = json_dict[PASSWORD_KEY]
        self.type = SSH_TYPE

    def to_dict(self):
        return {
                NAME_KEY: self.name,
                USERNAME_KEY: self.username,
                PASSWORD_KEY: self.password,
                TYPE_KEY: SSH_TYPE
        }


class SshKeyCredentials(Credentials):

    def __init__(self, json_dict):

        verify_keys(json_dict, required=[NAME_KEY, TYPE_KEY,
                USERNAME_KEY, SSHKEY_KEY], optional=[PASSWORD_KEY])

        self.name = json_dict[NAME_KEY]
        self.username = json_dict[USERNAME_KEY]
        self.key = json_dict[SSHKEY_KEY]
        self.type = SSH_KEY_TYPE

        # Password is optional for ssh keys.
        self.password = ''
        if PASSWORD_KEY in json_dict:
            self.password = json_dict[PASSWORD_KEY]

    def to_dict(self):
        return {
                NAME_KEY: self.name,
                USERNAME_KEY: self.username,
                PASSWORD_KEY: self.password,
                TYPE_KEY: SSH_KEY_TYPE,
                SSHKEY_KEY: self.key
        }


class Group(object):

    def __init__(self, name, ranges, credential_names, ports):
        """
        Create a group object.

        ranges is a list of strings specifying IP ranges. We just store the
        string.

        credential_names is a list of strings referencing credential *keys*.

        ports is a list of integers.
        """
        self.name = name
        self.ranges = ranges
        self.credential_names = credential_names
        self.ports = ports

    def to_dict(self):
        return {
                NAME_KEY: self.name,
                RANGE_KEY: self.ranges,
                CREDENTIALS_KEY: self.credential_names,
                PORTS_KEY: self.ports
        }


# Needs to follow the class definitions:
CREDENTIAL_TYPES = {
        SSH_TYPE: SshCredentials,
        SSH_KEY_TYPE: SshKeyCredentials
}


class ConfigBuilder(object):
    """
    Stateless object used to parse JSON into actual objects.

    Knows how to convert JSON text to dict, and form actual objects from those
    including validation checks to ensure the config is sane.

    Also converts the other direction turning objects into JSON text.
    """

    def build_config(self, json_text):
        """ Create Config object from JSON string. """
        config_dict = None
        try:
            config_dict = json.loads(json_text)
        except ValueError:
            raise BadJsonException

        verify_keys(config_dict, required=[VERSION_KEY, CREDENTIALS_KEY,
            GROUPS_KEY], optional=[])

        # Credentials needs to be parsed first so we can check that the groups
        # reference valid credential keys.
        credentials_dict = config_dict[CREDENTIALS_KEY]
        creds = self.build_credentials(credentials_dict)

        groups_dict = config_dict[GROUPS_KEY]
        groups = self.build_groups(groups_dict)

        config = Config(credentials=creds, groups=groups)

        return config

    def build_credentials(self, creds_list):
        """ Create a list of Credentials object. """
        creds = []
        for credentials_dict in creds_list:
            # Omit optional, will verify these once we know what class to
            # instantiate.
            verify_keys(credentials_dict, required=[NAME_KEY, TYPE_KEY])

            type_key = credentials_dict[TYPE_KEY]

            if type_key not in CREDENTIAL_TYPES:
                raise ConfigError("Unsupported credential type: %s",
                        credentials_dict[TYPE_KEY])

            creds_obj = CREDENTIAL_TYPES[type_key](credentials_dict)
            creds.append(creds_obj)
        return creds

    def build_groups(self, groups_list):
        """ Create a list of Credentials object. """

        groups = []
        for group_dict in groups_list:
            verify_keys(group_dict, required=[NAME_KEY, RANGE_KEY,
                CREDENTIALS_KEY, PORTS_KEY], optional=[])
            name = group_dict[NAME_KEY]
            ranges = group_dict[RANGE_KEY]
            credential_names = group_dict[CREDENTIALS_KEY]

            ports = []
            for p in group_dict[PORTS_KEY]:
                # Make sure we can cast to integers:
                try:
                    ports.append(int(p))
                except ValueError:
                    raise ConfigError("Invalid ssh port: %s" % p)

            group_obj = Group(name, ranges, credential_names, ports)
            groups.append(group_obj)

        return groups

    def dump_config(self, config):
        """ Returns JSON text for the given Config object. """
        config_dict = config.to_dict()
        json_text = json.dumps(config_dict)
        return json_text


