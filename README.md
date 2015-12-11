# PyDoS

This was written as a simple test for hammering a URL using GET or POST. The threading works pretty well (for Python) because the GIL can context-switch during the net calls.

# Benchmarks

On my VPS I was able to sustain 38-39 requests per second using PyDoS.

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

* Added support for GET or POST payloads (simply append the parameters to the URL as though it were a GET request)
