hyperglass-bird supports both BIRD versions 1.6 and 2.0.

# hyperglass-bird

hyperglass-bird is a restful API for the BIRD routing stack, for use by [hyperglass](https://github.com/checktheroads/hyperglass). hyperglass-bird ingests an HTTP POST request with JSON data and constructs 1 of 5 shell commands to run based on the passed parameters. For example:

```json
{
  "query_type": "ping",
  "afi": "ipv4",
  "source": "192.0.2.1",
  "target": "1.1.1.1"
}
```

Would construct (by default) `ping -4 -c 5 -I 192.0.2.1 1.1.1.1`, execute the command, and return the output as a string.

For BGP commands in version 1.6, BIRD's `birdc` and `birdc6` are used to get the output. For example:

```json
{
  "query_type": "bgp_route",
  "afi": "ipv6",
  "target": "2606:4700:4700::/48"
}
```
Would construct (by default) `birdc6 -r show route all where 2606:4700:4700::/48 ~ net`, execute the command, and return the output as a string.

BGP AS Path and Community queries are converted from "standard" hyperglass-supported syntax to BIRD's syntax:

```json
{
  "query_type": "bgp_aspath",
  "afi": "dual",
  "target": "_65000$"
}
```

Would construct `birdc -r show route all where bgp_path ~ [= * 65000 =]` and `birdc6 -r show route all where bgp_path ~ [= * 65000 =]` and concatenate the output for both commands.

## Installation

Currently, hyperglass-bird has only been tested on Ubuntu Server 18.04. A sample systemd service file is included to run hyperglass-bird as a service.

### Note

hyperglass-bird requires that `bird6` and `birdc6` be fully functional, even if IPv6 is not used.

### Clone the repository

```console
$ cd /opt/
$ git clone https://github.com/checktheroads/hyperglass-bird
```

### Install requirements

```console
$ cd /opt/hyperglass-bird/
$ pip3 install -r requirements.txt
```

### Install systemd service
```console
# cp /opt/hyperglass-bird/hyperglass-bird.service.example /etc/systemd/system/hyperglass-bird.service
# systemctl daemon-reload
# systemctl enable hyperglass-bird
```

### Update Permissions

```console
# chown -R bird:bird /opt/hyperglass-bird
```

### Generate API Key
```console
$ cd /opt/hyperglass-bird
$ python3 manage.py generate-key
Your API Key is: B3K1ckWUpwNyFU1F
Your Key Hash is: $pbkdf2-sha256$29000$9T5njNFaS6lVag1B6H2vFQ$mLEbQD5kOAgjfZZ1zEVlrke6wE8vBEHzK.zI.7MOAVo
```

Copy the API Key, in this example `B3K1ckWUpwNyFU1F` and add it to `configuration.toml`:

```toml
[api]
# listen_addr = "*"
# port = 8080
key = "B3K1ckWUpwNyFU1F"
```

If needed, you can uncomment the `listen_addr` or `port` varibales if you need to define a specific listen address or TCP port for hyperglass-bird to run on. For exmaple:

```toml
[api]
listen_addr = "10.0.1.1"
port = 8001
key = "B3K1ckWUpwNyFU1F"
```

In hyperglass, configure `devices.toml` to use the Key Hash (in this example `$pbkdf2-sha256$29000$9T5njNFaS6lVag1B6H2vFQ$mLEbQD5kOAgjfZZ1zEVlrke6wE8vBEHzK.zI.7MOAVo`) as your FRRouting device's password:

```toml
[router.'router1']
address = "10.0.0.1"
asn = "65000"
src_addr_ipv4 = "192.0.2.1"
src_addr_ipv6 = "2001:db8::1"
credential = "bird_api_router1"
location = "pop1"
display_name = "POP 1"
port = "8080"
type = "bird"
proxy = ""

[credential.'bird_api_router1']
username = "bird"
password = "$pbkdf2-sha256$29000$9T5njNFaS6lVag1B6H2vFQ$mLEbQD5kOAgjfZZ1zEVlrke6wE8vBEHzK.zI.7MOAVo"
```

## Start hyperglass-bird

```console
# systemctl restart hyperglass-bird
# systemctl status hyperglass-bird
```

## Test

hyperglass-bird should now be active, and you can run a simple test to verify that it is working apart from your main hyperglass implementation:

```python
>>> import json
>>> import requests
>>> query = '{"query_type": "bgp_route", "afi": "ipv4", "target": "1.1.1.0/24"}'
>>> query_json = json.dumps(query)
>>> headers = {'Content-Type': 'application/json', 'X-API-Key': '$pbkdf2-sha256$29000$m9M6R.j9HwMgJGRs7f0/Jw$5HERwfOIn3P0U/M9t5t04SmgRmTzk3435Lr0duqz07w'}
>>> url = "http://192.168.15.130:8080/bird"
>>> output = requests.post(url, headers=headers, data=query_json)
>>> print(output.text)
```
