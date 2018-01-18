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
import subprocess
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
