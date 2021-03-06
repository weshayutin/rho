#!/usr/bin/python

import subprocess
import unittest

from rho import rho_cmds


# for unit testing, we just run these locally

class _TestRhoCmd(unittest.TestCase):
    def setUp(self):
        self.rho_cmd = self.cmd_class()
        self.out = self._run_cmds()

    def _run_cmds(self):
        output = []
        for cmd in self.rho_cmd.cmd_strings:
            p = subprocess.Popen(cmd.split(' '), stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            out, err = p.communicate()
            output.append((out, err))
        return output

    def test_run(self):
        print self.out

    def test_parse(self):
        self.rho_cmd.populate_data(self.out)

    def test_data(self):
        self.rho_cmd.populate_data(self.out)
        print self.rho_cmd.data

class TestUnameCmd(_TestRhoCmd):
    cmd_class = rho_cmds.UnameRhoCmd

    def test_data_display(self):
        self.rho_cmd.populate_data(self.out)
        print "uname: %(uname.os)s\n hostname:%(uname.hostname)s\n%(uname.processor)s\n" % self.rho_cmd.data

class TestRedhatReleaseRhoCmd(_TestRhoCmd):
    cmd_class = rho_cmds.RedhatReleaseRhoCmd

    def test_data_display(self):
        self.rho_cmd.populate_data(self.out)
        print "name: %(redhat-release.name)s\n version:%(redhat-release.version)s\n%(redhat-release.release)s\n" % self.rho_cmd.data

class TestScriptRhoCmd(_TestRhoCmd):
    cmd_class = rho_cmds.ScriptRhoCmd
    def setUp(self):
        self.rho_cmd = self.cmd_class(command="ls -rho /tmp")
        self.out = self._run_cmds()

    
