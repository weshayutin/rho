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

""" Tests for the config module """

import unittest

from rho.config import *

SAMPLE_CONFIG1 = """
{
    "config": {

        "credentials": [

            {
                "name": "bobslogin",
                "type": "ssh",
                "username": "bob",
                "password": "sekurity"
            },

            {
                "name": "bobskey",
                "type": "ssh_key",
                "username": "bob",
                "key": "-----BEGIN RSA PRIVATE KEY-----\\nProc-Type: 4,ENCRYPTED\\nDEK-Info:\\nBLHABLAHBLAHBLAH\\n-----END RSA PRIVATE KEY-----",
                "password": "sekurity"
            }

        ],

        "groups": [

            {
                "name": "accounting",
                "range": [
                    "192.168.0.0/24",
                    "192.168.1.1-192.168.1.10",
                    "192.168.5.0"
                ],
                "credentials": ["bobskey", "bobslogin"],
                "ports": [22, 2222]
            },

            {
                "name": "it",
                "range": [
                    "192.168.9.0/24"
                ],
                "credentials": ["bobskey"]
            }

        ]

    }
}
"""


class ConfigParsingTests(unittest.TestCase):

    def setUp(self):
        self.builder = ConfigBuilder()

    def test_bad_json_string(self):
        bad_json = "does this look valid to you?"
        self.assertRaises(BadJsonException, self.builder.build_config, bad_json)

    def test_json_config_key(self):
        """ Verify top level of JSON hash is just a config key. """
        self.assertRaises(ConfigurationException, self.builder.build_config,
                "{}")
        self.assertRaises(ConfigurationException, self.builder.build_config,
                "{}")

    def test_build_sample_config(self):
        config = self.builder.build_config(SAMPLE_CONFIG1)
        self.assertEquals(2, len(config.credentials))

class ConfigParsingTests(unittest.TestCase):

    def setUp(self):
        self.builder = ConfigBuilder()
        self.credentials_hash = [
                {
                    "name": "ansshlogin",
                    "type": "ssh",
                    "username": "bob",
                    "password": "password"
                },
                {
                    "name": "ansshkey",
                    "type": "ssh_key",
                    "key": "whatever",
                    "username": "bob",
                    "password": "password"
                },
        ]

    def test_build_credentials(self):
        creds = self.builder.build_credentials(self.credentials_hash)
        self.assertEquals(2, len(creds))
        self.assertEquals("ansshlogin", creds[0].name)
        self.assertEquals(SshCredentials, type(creds[0]))

        self.assertEquals("ansshkey", creds[1].name)
        self.assertEquals(SshKeyCredentials, type(creds[1]))

    def test_build_credentials_bad_type(self):
        self.credentials_hash[0]["type"] = "badtype"
        self.assertRaises(ConfigurationException,
                self.builder.build_credentials, self.credentials_hash)

    def test_build_credentials_missing_type(self):
        self.credentials_hash[0].pop("type")
        self.assertRaises(ConfigurationException,
                self.builder.build_credentials, self.credentials_hash)

    def test_build_credentials_missing_username(self):
        self.credentials_hash[0].pop("username")
        self.assertRaises(ConfigurationException,
                self.builder.build_credentials, self.credentials_hash)

    def test_build_credentials_key_no_passphrase(self):
        # I think we're going to support a passphraseless key for now:
        self.credentials_hash[1].pop("password")
        self.builder.build_credentials(self.credentials_hash)


class MiscTests(unittest.TestCase):

    def test_verify_keys(self):
        verify_keys({'a': 1, 'b': 2}, required=['a'], optional=['b'])

    def test_verify_keys_all_optional(self):
        verify_keys({'a': 1, 'b': 2}, optional=['a', 'b'])

    def test_verify_keys_all_required(self):
        verify_keys({'a': 1, 'b': 2}, required=['a', 'b'])

    def test_verify_keys_missing_required(self):
        self.assertRaises(ConfigurationException,
                verify_keys, {'b': 2}, required=['a'], optional=['b'])

    def test_extraneous_keys(self):
        self.assertRaises(ConfigurationException, verify_keys, 
                {'a': 1, 'b': 2}, required=['a'], optional=[])

    def test_only_check_required(self):
        # b is ignored because we didn't specify optional keys.
        verify_keys({'a': 1, 'b': 2}, required=['a'])

