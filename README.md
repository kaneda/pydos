# PyDoS

This was written as a simple test for hammering a URL using GET or POST. The threading works pretty well (for Python) because the GIL can context-switch during the net calls.

# Benchmarks

Using a c4.2xlarge (8 vCPU, 15GB vRAM) instance in Amazon and 20 threads you can use this tool to generate 20K-30K RPM (or 330-500 requests per second).

On my VPS (1 vCPU, 2GB vRAM) I was able to generate 2.2K-2.5K RPM (or 38-39 requests per second) using PyDoS.

# Options

| Flag | Description | Default | Notes
| :-----------: | :-----------  | :----------- | :-----
| --help | Print this help | N/A | |
| -u, --url | url to DoS | N/A | Should include the protocol |
| --timeout-http | Timeout for HTTP(S) socket connections | 0.5 seconds (500ms) | Minimum is 0.1 seconds
| --time-to-run | Time in total to run | 600 seconds | Minimum is 1 second
| --num-threads | Number of threads to use | 1 thread | Minimum is 1 thread
| --method | Method to use | GET | Must be one of 'POST' or 'GET'
| --verbose | Turn on verbose information about things happening in each thread | Off | Takes no arguments

# Examples:

```bash
python pydos.py -u https://yourdomain.com/somepath --time-to-run=600               # Run against your domain for 600 seconds
python pydos.py -u https://yourdomain.com/somepath --method=POST                   # Run POST calls
python pydos.py -u https://yourdomain.com/somepath --verbose                       # Enable verbose mode
python pydos.py -u https://yourdomain.com/somepath?somearg=somevalue --method=POST # Run POST called against endpoint with payload somearg=somevalue
```

# Recent Changes

* Transitioned the project to Python3, cleaning up a lot of the code in the process
* Fixed payload support for values that contain the "=" sign
* Fixed payload in URL for POST requests to protect integrity of request
* Benchmarked using larger machine against production service(s)
* Added support for GET or POST payloads (simply append the parameters to the URL as though it were a GET request)
