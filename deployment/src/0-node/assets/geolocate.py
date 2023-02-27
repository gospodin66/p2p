import json
import subprocess
def call_curl(args):
    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return json.loads(stdout.decode('utf-8'))
url = "https://geolocation-db.com/json/"
cmd = [
    "curl",
    "-vvv",
    "-s",
    # "--socks5-hostname",
    # "127.0.0.1:9050",
    url
]
data = call_curl(cmd)
print(data)
link = f"http://www.google.com/maps/place/{data['latitude']},{data['longitude']}"
print(link)