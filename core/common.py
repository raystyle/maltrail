#!/usr/bin/env python

"""
Copyright (c) 2014-2015 Miroslav Stampar (@stamparm)
See the file 'LICENSE' for copying permission
"""

import csv
import gzip
import os
import re
import StringIO
import subprocess
import urllib
import urllib2
import zipfile
import zlib

from core.settings import NAME
from core.settings import TIMEOUT
from core.settings import TRAILS_FILE

def retrieve_content(url, data=None):
    """
    Retrieves page content from given URL
    """

    try:
        req = urllib2.Request("".join(url[i].replace(' ', "%20") if i > url.find('?') else url[i] for i in xrange(len(url))), data, {"User-agent": NAME, "Accept-encoding": "gzip, deflate"})
        resp = urllib2.urlopen(req, timeout=TIMEOUT)
        retval = resp.read()
        encoding = resp.headers.get("Content-Encoding")

        if encoding:
            if encoding.lower() == "deflate":
                data = StringIO.StringIO(zlib.decompress(retval, -15))
            else:
                data = gzip.GzipFile("", "rb", 9, StringIO.StringIO(retval))
            retval = data.read()
    except Exception, ex:
        retval = ex.read() if hasattr(ex, "read") else getattr(ex, "msg", str())

    return retval or ""

def check_sudo():
    """
    Checks for sudo/Administrator privileges
    """

    check = None

    if not subprocess.mswindows:
        if getattr(os, "geteuid"):
            check = os.geteuid() == 0
    else:
        import ctypes
        check = ctypes.windll.shell32.IsUserAnAdmin()

    return check

def extract_zip(filename, path=None):
    _ = zipfile.ZipFile(filename, 'r')
    _.extractall(path)

def addr_to_int(value):
    _ = value.split('.')
    return (long(_[0]) << 24) + (long(_[1]) << 16) + (long(_[2]) << 8) + long(_[3])

def int_to_addr(value):
    return '.'.join(str(value >> n & 0xff) for n in (24, 16, 8, 0))

def make_mask(bits):
    return 0xffffffff ^ (1 << 32 - bits) - 1

def get_regex(items):
    head = {}

    for item in sorted(items):
        current = head
        for char in item:
            if char not in current:
                current[char] = {}
            current = current[char]
        current[""] = {}

    def process(current):
        if not current:
            return ""

        if not any(current[_] for _ in current):
            if len(current) > 1:
                items = []
                previous = None
                start = None
                for _ in sorted(current) + [unichr(65535)]:
                    if previous is not None:
                        if ord(_) == ord(previous) + 1:
                            pass
                        else:
                            if start != previous:
                                print start, previous
                                if start == '0' and previous == '9':
                                    items.append(r"\d")
                                else:
                                    items.append("%s-%s" % (re.escape(start), re.escape(previous)))
                            else:
                                items.append(re.escape(previous))
                            start = _
                    if start is None:
                        start = _
                    previous = _

                return ("[%s]" % "".join(items)) if len(items) > 1 or '-' in items[0] else "".join(items)
            else:
                return re.escape(current.keys()[0])
        else:
            return ("(?:%s)" if len(current) > 1 else "%s") % ('|'.join("%s%s" % (re.escape(_), process(current[_])) for _ in sorted(current))).replace('|'.join(str(_) for _ in xrange(10)), r"\d")

    regex = process(head).replace(r"(?:|\d)", r"\d?")

    return regex

def retrieve_file(url, filename=None):
    try:
        filename, _ = urllib.urlretrieve(url, filename)
    except:
        filename = None
    return filename

def load_trails(quiet=False):
    if not quiet:
        print "[i] loading trails file..."

    retval = {}

    if os.path.isfile(TRAILS_FILE):
        try:
            with open(TRAILS_FILE, "rb") as f:
                reader = csv.reader(f, delimiter=',', quotechar='\"')
                for row in reader:
                    if row:
                        trail, info, reference = row
                        retval[trail] = (info, reference)

        except Exception, ex:
            exit("[x] something went wrong during trails file read '%s' ('%s')" % (TRAILS_FILE, ex))

    if not quiet:
        _ = len(retval)
        try:
            _ = '{0:,}'.format(_)
        except:
            pass
        print "[i] %s trails loaded" % _

    return retval
