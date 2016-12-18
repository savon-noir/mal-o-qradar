#!/usr/bin/env python

from malfeeds.objects import MalFeedsCollection, MalFeed
import ConfigParser
import argparse
import glob
import os
import sys
from q import qapi

from pprint import pprint


class MalOQ(object):
    def __init__(self, confdir=None, enabled_feeds=False):
        self.feedsconfig = self.load_configs(confdir, enabled_feeds)
        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.qapi = self.load_api_config(base_dir + "/api.ini")

    def load_api_config(self, conffile=None):
        pconfig = None
        rval = None
        if conffile is not None and os.path.isfile(conffile):
            try:
                pconfig = ConfigParser.ConfigParser()
                pconfig.read(conffile)
            except ConfigParser.ParsingError as e:
                print("error while parsing configuration file: {0}".format(e))
        else:
            print("error: configuration file {0} does not exists".format(conffile))
        if pconfig is not None:
            ccheck = True
            if pconfig.getint('api', 'cert_check') == 0:
                ccheck = False
            cdict = {'server': pconfig.get('api', 'server'), 'token': pconfig.get('api', 'token'), 'cert_check': ccheck}
            rval = qapi(**cdict)
        return rval
    
    def load_configs(self, confdir=None, enabled_feeds=False):
        if confdir is not None:
            base_dir = confdir
        else:
            base_dir = os.path.dirname(os.path.realpath(__file__)) + '/feeds/'
        feedslist = glob.glob("{0}/*.ini".format(base_dir))

        feedsconfig = self._config_parser(feedslist, enabled_feeds)
        return feedsconfig

    def _config_parser(self, feedslist, enabled_feeds=False):
        try:
            feedsconfig = ConfigParser.ConfigParser()
            feedsconfig.read(feedslist)
        except ConfigParser.ParsingError as e:
            print("error while parsing feeds: {0}".format(e))

        for section in feedsconfig.sections():
            if enabled_feeds is True and feedsconfig.getint(section, "enabled") == 0:
                feedsconfig.remove_section(section)
            else:
                feedsconfig.set(section, "name", section)

        return feedsconfig

    def create_collection(self):
        mfcollection = MalFeedsCollection()

        for section in self.feedsconfig.sections():
            mfsection = dict(self.feedsconfig.items(section))
            try:
                _mf = MalFeed(mfsection)
                mfcollection.add(_mf)
            except Exception, e:
                print("error while creating malfeed: {0}".format(str(e)))

        return mfcollection


def main(args):
    feedsfactory = MalOQ()
    mfcollection = feedsfactory.create_collection()
    for malfeed in mfcollection.list():
        if malfeed.enabled:
            print("{0},{1}".format(malfeed.name, malfeed.feedurl))
        #    pprint(malfeed.feed_header)
            if args.dry_run:
               continue
            malfeed.update()
            for mentry in malfeed.feed_entries:
                if mentry.type == 'ip':
                    feedsfactory.qapi.add_set_item('blacklist_ip_info', mentry.ip, item_source=malfeed.name)
                elif mentry.type == 'domain':
                    feedsfactory.qapi.add_set_item('blacklist_dom_info', mentry.domain, item_source=malfeed.name)
                else:
                    print("unknown type {0}".format(mentry.type))


def check_usage():
    avalid = True
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--dry-run', help='only dump enabled feeds without running', action='store_true')
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = check_usage()
    try:
        main(args)
    except KeyboardInterrupt:
        sys.exit()
