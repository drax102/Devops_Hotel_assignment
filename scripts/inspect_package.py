import re
import urllib.request

url = "https://github.com/drax102/Devops_Hotel_assignment/pkgs/container/devops_hotel_assignment"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8")

matches = re.findall(r"ghcr\.io/drax102/devops_hotel_assignment[^\s\"']*", html)
print("Pointers on package page:")
for m in sorted(set(matches)):
    print(" -", m)
