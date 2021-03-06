#!/usr/bin/env python
# encoding: utf-8

# Created by Onur Senture
# Version 0.25
# Put.io Paid Site Checker

"""

- Takes paysite URL from paysites.txt.
- Username, password and user_id can be changed from the top of code.
- Platform should be specified to check md5 values correctly. (Unix, or Win)
- Error priority is like that: fetch > file not found > checksum
- Initial deletion of files on putio handling with bash script.
- Deletion of /tmp folder content after test is also handling with bash script.

--only:

    if you want to use "--only" parameter, take string between // and / in the url
    text file input: http://rapidshare.com/files/414210082/rapidshare_test_putio.txt.html
    usage: python paidsitecheck.py --only=rapidshare.com

"""

#TODO: github test
#TODO: api timeout problem
#TODO: too long "connecting to resources", it can cause api server connection error
#TODO: add manual parameter, and manual menu
#TODO: torrent can be added in the future

import putio
import sys
import hashlib
import time
import pycurl
import re
import optparse

username = "paidsitetester"
password = "ps0216"
secret = "45glum394"
user_id = "8536"
platform = "unix"
paysite_list = ["rapidshare", "storageto", "netload", "mediafire", "uploadedto", "megaupload", "fileserve", "hotfile"]
file_limit = 20

class Paysite():
    def __init__(self):
        self.status = "ok"
        self.error_type = "not defined"

class Downloader:
    def __init__(self):
        self.contents = ''

    def body_callback(self, buf):
        self.contents = self.contents + buf

    def fetch(self, url, username, password):
        print "dowloading: %s" % url
        c = pycurl.Curl()
        c.setopt(c.URL, "%s" % url)
        c.setopt(c.WRITEFUNCTION, self.body_callback)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.UNRESTRICTED_AUTH, True)
        c.setopt(c.VERBOSE, False)
        c.setopt(c.TIMEOUT, 120)
        c.setopt(c.USERPWD, '%s:%s' % (username,password) )
        c.setopt(c.HTTPAUTH, c.HTTPAUTH_BASIC)
        c.perform()
        c.close()
        return self.contents

def connect_api():
    try:
        api = putio.Api(api_key=username, api_secret=secret)
        return api
    except:
        print "api server connect error"
        sys.exit(0)

def seperate():
    print "--------------------------------"

# takes file and returns its md5
def md5file(fileName):
    m = hashlib.md5()
    try:
        fd = open(fileName, "rb")
    except IOError:
        print "file not found", filename
        return
    content = fd.readlines()
    fd.close()
    for eachLine in content:
        m.update(eachLine)
    return m.hexdigest()

# download files from paysites to put.io
def fetch(api, test_only):
    pay_sites = [line.strip() for line in open('paysites.txt')]
    if test_only:
        for site in pay_sites:
            # take string between // and / from the url and compare with --only parameter
            if(str(test_only)==re.split('/', site)[2]):
                fetch_base(api, site)
    else:
        for site in pay_sites:
            fetch_base(api, site)
    seperate()
    print "fetching is not finished yet. please wait..."

# internal function takes link to fetch
def fetch_base(api, site):
    print "fetching %s" % site
    try:
        bucket = api.create_bucket()
        bucket.analyze([site])
        bucket.fetch()
    except:
        print "api server connect error (fetch_base)"
        sys.exit(0)

# wait until all transfers in putio is done
def wait(api):
    try:
        trans = api.get_transfers()
    except:
        print "api server connect error (wait)"
        sys.exit(0)
    if trans:
        time.sleep(5)
        error_finder(trans)
        wait(api)

def check_on_putio(api, test_only):
    seperate()
    if test_only:
        paysites = [str(test_only).split('.')[0]]
    else:
        paysites = paysite_list
    try:
        #TODO: if there is no file on putio, it will not work. 
        items = api.get_items()
    except:
        print "api server connect error (check_on_putio)"
        sys.exit(0)
    for site in paysites:
        control_flag = 0
        for it in items:
            if re.split('_', str(it.name))[0] == site:
                control_flag = 1
                print  "%s --> ok (fetch)" % site
        if control_flag == 0:
            print "%s --> error (fetch)" % site
            exit_code = 0

# downloading file to local space
def download_to_local(api):
    seperate()
    try:
        items = api.get_items(limit=file_limit, offset=0)
    except:
        print "api server connect error (download_to_local)"
        sys.exit(0)
    for it in items:
        d = Downloader()
        url = 'http://put.io/download-file/' + user_id + '/' + str(it.id)
        content = d.fetch(url , username, password)
        file_handler = open('tmp/' + it.name , 'w')
        file_handler.write(content)
        file_handler.close()

# calculate md5's and check
def check_local_md5(api):
    #TODO: ySANHZc --> error (checksum)
    seperate()
    if platform == "unix":
        check_md5 = md5file('checksum_unix.txt')
    else:
        check_md5 = md5file('checksum_win.txt')
    try:
        items = api.get_items(limit=file_limit, offset=0)
    except:
        print "api server connect error (check_local_md5)"
        sys.exit(0)
    for it in items:
        status = "ok"
        temp_md5 = md5file('tmp/' + it.name)
        if temp_md5 != check_md5:
            exit_code = 0
            status = "error"
        print '%s --> %s (checksum)' % (re.split('_', str(it.name))[0], status)

# delete all files from putio file space
def delete_files(api):
    seperate()
    try:
        items = api.get_items(limit=(file_limit*5), offset= 0)
    except:
        print "api server connect error (delete_files)"
        sys.exit(0)
    for it in items:
        it.delete_item();
    print 'deletion is succesfully done'

# report if item gives error during fetch process
def error_finder(trans):
    for t in trans:
        if str(t.status) == "Error":
            print "\n%s --> error (file not found)" % re.split('_', str(t.name))[0]
            t.destroy_transfer()
            exit_code = 0

if __name__== '__main__':

    api = connect_api()
    exit_code = 1
    parser = optparse.OptionParser()
    parser.add_option('--only', help = "test only specific paysite")
    (opts, args) = parser.parse_args()

    fetch(api ,opts.only)
    wait(api)
    check_on_putio(api, opts.only)
    download_to_local(api)
    check_local_md5(api)
    delete_files(api)


    """
    paysite_list = []


    rapidshare = Paysite()

    paysite_list.append(rapidshare)

    paysite_list[0].error_type = "asdasdasdasdasdasda"

    print rapidshare.status
    print rapidshare.error_type


    #hotfile.status = "error"
    """

    sys.exit(exit_code)