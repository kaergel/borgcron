#!/usr/bin/python3
# -*- coding: utf-8 -*-

# author: Thomas Kaergel kaergel at b1-systems.de>
# last-modified:: 2019-01-17
# purpose: backupscript for use with cron and borg
# name: borgcron

import os
import datetime
import argparse
import sys
import yaml
import logging
import re
import socket
import struct
import subprocess
import sys
import time

defaultlogfile = 'borgcron.log'
defaultloglevel = logging.WARNING

LOG = logging.getLogger(__name__)

class options(object):
    def __init__(self):	
        self._init_parser()

    def _init_parser(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-s', "--stdout",
                                 help='print log to stdout too',
                                 action='store_true')
        self.group = self.parser.add_mutually_exclusive_group(required=False)
        self.group.add_argument('-d', '--debug',
                                help="print lots of debugging statements",
                                action="store_const",
                                default=defaultloglevel,
                                dest="loglevel", const=logging.DEBUG)
        self.group.add_argument('-v', '--verbose',
                                help="be verbose",
                                action="store_const",
                                default=defaultloglevel,
                                dest="loglevel", const=logging.INFO)
        self.parser.add_argument('-p', "--pretend",
                                 help='nothing is really done! '
                                      'borgcron just generates the borg '
                                      'command-lines, prints them to stdout'
                                      'and exits',
                                 action='store_true')
        self.parser.add_argument('configfile',
                                 nargs='?',
                                 type=argparse.FileType('r'),
                                 default=sys.stdin,
                                 help='a config file in YAML format.'
                                      ' Can also be read from stdin.')
        self.parser.add_argument('-l', "--logfile",
                                 metavar='logfile',
                                 # nargs='*',
                                 type=argparse.FileType('a'),
                                 default=defaultlogfile,
                                 help='default logfile is borgcron.log')

    def parse(self, args=None):
        return self.parser.parse_args(args)


class clicommand(object):
    def __init__(self, cmdline, logfile):
        self._cmdline = cmdline
        self._logfile = logfile

    def execute(self):
        LOG.info("executing cli-command: \n")
        proc = subprocess.Popen(self._cmdline,
                                stdout = self._logfile,
                                stderr = subprocess.STDOUT,
                                universal_newlines = True,
                                shell = False)
        returncode = proc.wait()
        LOG.info("command returned: %s" % returncode)
        return returncode


class backupdir(object):
    def __init__(self, directory):
        self._name = directory["name"]
        self._days = directory["days"]
        self._month = directory["month"]
        self._years = directory["years"]
        self._namedepth = directory["namedepth"]

    def _get_title(self):
        LOG.debug("_get_title says self._name is %s" % self._name)
        title = ""
        path = self._name
        depth = self._namedepth
        while path is not "/" and depth > -1:
            path, folder = os.path.split(path)
            LOG.debug("path prefix is %s. foldername is %s" % (path, folder))
            if depth > 0:
                title = "°" + folder + title
            else:
                title = folder + title
            depth -= 1
        LOG.debug("title is: %s" % title)
        return title

    def generate_cmds(self, args, flags, comp, repo):
        LOG.info("Starting backup of directroy %s" % self._name)
        LOG.debug("pretend is: %s" % args.pretend)
        now = datetime.datetime.today().strftime('%Y-%m-%d_%H%M%S')
        create = ['/usr/local/bin/borg', 'create', '-C']
        create += [comp]
        create += flags.split()
        create += [repo + '::' + self._get_title() + '-' + now]
        create += [self._name]
        LOG.info("generated borg create command is:")
        LOG.info(create)
        prune = ['/usr/local/bin/borg', 'prune']
        prune += flags.split()
        prune += '-d', str(self._days)
        prune += '-m', str(self._month)
        prune += '-y', str(self._years)
        prune += repo,
        prune += '-P', self._get_title()
        LOG.info("generated borg prune command is:")
        LOG.info(prune)
        return create, prune


def wake_on_lan(cfg):

    LOG.info("Sending WakeOnLAN magic paket.")
    mac_str = cfg["config"]["wol_mac_address"]
    net_bcast = cfg["config"]["remote_bcast_address"]
    addr_byte = mac_str.split(':')
    hw_addr = struct.pack('BBBBBB', int(addr_byte[0], 16),
                                    int(addr_byte[1], 16),
                                    int(addr_byte[2], 16),
                                    int(addr_byte[3], 16),
                                    int(addr_byte[4], 16),
                                    int(addr_byte[5], 16))
    msg = b'\xff' * 6 + hw_addr * 16
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(msg, (net_bcast, 7))
    sock.sendto(msg, (net_bcast, 9))
    sock.close()
    return


def check_server(cfg):

    LOG.info("Checking if ssh on remote host is listening... plz wait")
    wol_ip = cfg["config"]["remote_host_address"]
    sock = socket.socket()
    count = 0
    res = sock.connect_ex((wol_ip, 22))
    while res != 0 and count < 300:
        time.sleep(1)
        count += 1
        sock.close()
        sock = socket.socket()
        res = sock.connect_ex((wol_ip, 22))
    if res != 0:
        LOG.critical("Remote host did not come up!")
        exit(1)
    LOG.info("Remote host is now up!")
    time.sleep(3)
    return


def configlogger(args):
    LOG.setLevel(defaultloglevel)
    logfile = open(args.logfile.name, 'a')
    fh = logging.StreamHandler(logfile)
    fh.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s'))
    LOG.addHandler(fh)
    if args.stdout:
        LOG.warn('duplicating log to stdout')
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
                        '%(asctime)s - '
                        '%(levelname)s - %(message)s'))
        LOG.addHandler(ch)
    LOG.warn('-' * 80)
    LOG.warn("borgcron by Thomas Kärgel - starting new backup run")
    LOG.warn('Switching to loglevel %s' % args.loglevel)
    LOG.setLevel(args.loglevel)
    return logfile


def parseconfig(args):
    if os.path.isfile(args.configfile.name):
        LOG.info("Reading YAML config from file")
        stream = open(args.configfile.name, 'r')
    else:
        LOG.warn("Awaiting YAML config from stdin")
        stream = sys.stdin
    try:
        config = yaml.load(stream)
        LOG.debug("YAML config is:\n" + yaml.dump(config,
                                                  explicit_start=True,
                                                  default_flow_style=False))
    except yaml.YAMLError as exc:
        logging.critical(exc)
        exit(1)
    return config


def pretendoutput(createcmd, prunecmd):
    createstr = ''
    for i in createcmd:
        createstr = createstr + str(i) + ' '
    print("-" * 80)
    print("create command is:")
    print(createstr)
    prunestr = ''
    for i in prunecmd:
        prunestr = prunestr + str(i) + ' '
    print("-" * 80)
    print("prune command is:")
    print(prunestr)


def main():
    args = options().parse()
    logfile = configlogger(args)
    LOG.debug("args:\n" + str(args))
    cfg = parseconfig(args)
    repo = cfg["config"]["target_repository"]
    comp = cfg["config"]["compression"]
    flags = cfg["config"]["borg_options"]
    prescript = cfg["config"]["prerun_script"]
    if cfg["config"]["wake_remote_host"] and not args.pretend:
        wake_on_lan(cfg)
        check_server(cfg)
    LOG.debug("prescript is: %s" % prescript.split())
    if prescript != "":
        returncode = clicommand(prescript.split(), logfile).execute()
        if returncode == 1:
            LOG.critical("execution of prerun_script failed! -> bailing out.")
            exit(1)
    if "directories" in cfg["config"]:
        for directory in cfg["config"]["directories"]:
            LOG.debug("item config is:\n" +
                      yaml.dump(directory,
                                explicit_start=True,
                                default_flow_style=False))
            dir_item = backupdir(directory)
            LOG.debug("dir_item.name is %s" % dir_item._name)
            createcmd, prunecmd = dir_item.generate_cmds(args, flags, comp, repo)
            if args.pretend:
                pretendoutput(createcmd, prunecmd)
            else:
                clicommand(createcmd, logfile).execute()
                if directory["prune"]:
                    clicommand(prunecmd, logfile).execute()
    if cfg["config"]["shutdown_remote_host"]:
        sshtarget = repo.split(':')
        shutdowncmd = ("ssh %s %s" % (sshtarget[0],
                       cfg["config"]["shutdown_command"]))
        LOG.debug("shutdowncmd is: %s" % shutdowncmd)
        if not args.pretend:
            LOG.info("Shuting down remote host.")
            returncode = clicommand(shutdowncmd.split(),
                                    logfile).execute()
            if returncode == 1:
                LOG.critical("Shutdown of remote failed!")
                exit(1)
    postscript = cfg["config"]["postrun_script"]
    LOG.debug("postscript is: %s" % postscript.split())
    if postscript != "":
        returncode = clicommand(postscript.split(), logfile).execute()
        if returncode == 1:
            LOG.critical("execution of postrun_script failed! -> bailing out.")
            exit(1)



if __name__ == "__main__":
    main()
    exit(0)
