# vim: et:sta:bs=2:sw=4:
""" Stresstest tkbd by pushing a lot of random occupation changes. """

import sys
import time
import json
import random
import httplib

STATI = [{'status': 'offline'},
         {'status': 'used', 'session': 'windows'},
         {'status': 'used', 'session': 'linux'},
         {'status': 'free', 'session': 'windows'},
         {'status': 'free', 'session': 'linux'},
         {'status': 'unknown', 'session': 'linux'},
         {'status': 'unknown', 'session': 'windows'},
         {'status': 'unknown'}]

PCS = ["bibpc44", "hg201pc28", "hg201pc29", "hg201pc26", "hg201pc27",
    "hg201pc24", "hg201pc25", "hg201pc22", "hg201pc23", "hg201pc20",
    "hg201pc21", "hg075pc43", "hg075pc42", "hg075pc41", "hg075pc40",
    "hg023pc19", "hg023pc18", "hg075pc45", "hg075pc44", "hg023pc15",
    "hg023pc14", "hg023pc17", "hg023pc16", "hg023pc11", "hg023pc10",
    "hg023pc13", "hg023pc12", "hg075pc17", "hg137pc48", "hg029pc12",
    "hg137pc44", "hg137pc45", "hg137pc46", "hg137pc47", "hg137pc40",
    "hg137pc41", "hg137pc42", "hg137pc43", "hg201pc01", "hg206pc14",
    "hg206pc15", "hg206pc16", "hg206pc17", "hg206pc10", "hg206pc11",
    "hg206pc12", "hg206pc13", "hg206pc18", "hg206pc19", "hg029pc57",
    "hg029pc56", "hg029pc55", "hg029pc54", "hg029pc53", "hg029pc52",
    "hg029pc51", "hg029pc50", "hg075pc47", "hg029pc59", "hg075pc46",
    "hg201pc04", "hg201pc05", "hg201pc06", "hg201pc07", "bibpc58", "bibpc59",
    "hg201pc02", "hg201pc03", "bibpc54", "bibpc55", "bibpc56", "bibpc57",
    "bibpc50", "bibpc51", "bibpc52", "bibpc53", "hg137pc39", "hg137pc38",
    "hg023pc31", "hg023pc30", "hg023pc37", "hg023pc36", "hg023pc35",
    "hg023pc34", "hg137pc31", "hg137pc30", "hg137pc33", "hg137pc32",
    "hg137pc35", "hg137pc34", "hg137pc37", "hg137pc36", "hg075pc48",
    "hg761pc09", "hg761pc08", "hg761pc03", "hg761pc02", "hg761pc01",
    "hg761pc07", "hg761pc06", "hg761pc05", "hg761pc04", "hg075pc32",
    "hg075pc33", "hg075pc30", "hg075pc31", "hg075pc36", "hg075pc37",
    "hg075pc34", "hg075pc35", "hg029pc35", "hg029pc34", "hg075pc38",
    "hg075pc39", "hg029pc31", "hg029pc30", "hg029pc33", "hg029pc32",
    "hg023pc27", "bibpc48", "hg137pc19", "hg137pc18", "hg137pc17",
    "hg137pc16", "hg137pc15", "hg137pc14", "hg137pc13", "hg137pc12",
    "hg137pc11", "hg137pc10", "hg023pc26", "hg023pc28", "hg023pc29",
    "hg075pc60", "hg075pc18", "hg075pc19", "hg075pc10", "hg075pc11",
    "hg075pc12", "hg075pc13", "hg075pc14", "hg075pc15", "hg075pc16",
    "hg029pc38", "hg029pc13", "hg029pc21", "hg023pc40", "hg029pc10",
    "hg029pc17", "hg029pc16", "hg029pc15", "hg029pc14", "hg029pc19",
    "hg029pc18", "hg029pc11", "hg029pc37", "hg029pc36", "hg206pc29",
    "hg206pc28", "hg206pc25", "hg206pc24", "hg206pc27", "hg206pc26",
    "hg206pc21", "hg206pc20", "hg206pc23", "hg206pc22", "hg023pc38",
    "bibpc45", "hg029pc04", "hg137pc00docent", "hg201pc38", "hg029pc05",
    "hg201pc35", "hg201pc34", "hg201pc37", "hg201pc36", "hg201pc31",
    "hg201pc30", "hg201pc33", "hg201pc32", "hg029pc07", "hg153pc02",
    "hg153pc03", "hg153pc01", "hg153pc06", "hg153pc07", "hg153pc04",
    "hg153pc05", "hg153pc08", "hg153pc09", "hg075pc52", "hg206pc03",
    "hg206pc02", "hg206pc01", "hg206pc07", "hg206pc06", "hg206pc05",
    "hg206pc04", "hg075pc58", "hg206pc09", "hg206pc08", "hg075pc59",
    "hg029pc60", "hg023pc41docent", "hg201pc13", "hg201pc12", "hg201pc11",
    "hg201pc10", "hg201pc17", "hg201pc16", "hg201pc15", "hg201pc14",
    "bibpc47", "bibpc46", "hg201pc19", "hg201pc18", "bibpc43", "bibpc42",
    "bibpc41", "hg075pc54", "hg075pc55", "hg075pc56", "hg075pc57",
    "hg075pc50", "hg075pc51", "hg023pc08", "hg023pc09", "hg023pc06",
    "hg023pc07", "hg023pc04", "hg023pc05", "hg023pc02", "hg023pc03",
    "hg023pc01", "bibpc32", "bibpc30", "bibpc31", "hg029pc39", "hg075pc21",
    "hg029pc49", "hg075pc23", "hg075pc22", "hg075pc25", "hg075pc24",
    "hg075pc27", "hg075pc26", "hg029pc40", "hg075pc28", "hg029pc42",
    "hg029pc43", "hg029pc44", "hg029pc45", "hg029pc46", "hg029pc47",
    "hg075pc49", "bibpc69", "bibpc68", "bibpc61", "bibpc60", "bibpc63",
    "bibpc62", "bibpc65", "bibpc64", "bibpc67", "bibpc66", "hg023pc24",
    "hg023pc25", "hg137pc28", "hg137pc29", "hg023pc20", "hg023pc21",
    "hg023pc22", "hg023pc23", "hg137pc22", "hg137pc23", "hg137pc20",
    "hg137pc21", "hg137pc26", "hg137pc27", "hg137pc24", "hg137pc25",
    "hg075pc01docent", "hg029pc58", "hg761pc18", "hg075pc09", "hg761pc14",
    "hg761pc15", "hg761pc16", "hg761pc17", "hg761pc10", "hg761pc11",
    "hg761pc12", "hg761pc13", "hg075pc07", "hg075pc06", "hg075pc05",
    "hg075pc04", "hg075pc03", "hg075pc02", "hg029pc28", "hg029pc29",
    "hg029pc26", "hg029pc27", "hg029pc24", "hg029pc25", "hg029pc22",
    "hg029pc23", "hg029pc20", "hg075pc08", "infopc04", "infopc03",
    "infopc02", "infopc01", "hg201pc08", "hg201pc09", "hg137pc01",
    "hg137pc02", "hg137pc03", "hg137pc04", "hg137pc05", "hg137pc06",
    "hg137pc07", "hg137pc08", "hg137pc09", "hg023pc33", "hg023pc32",
    "hg029pc61docent", "bibpc49", "hg201pc41", "hg201pc42", "hg201pc43",
    "hg075pc65", "hg075pc64", "hg075pc61", "hg023pc39", "hg075pc63",
    "hg075pc62", "hg153pc11", "hg153pc10", "hg029pc06", "hg153pc12",
    "hg029pc01", "hg029pc02", "hg029pc03", "hg029pc08", "hg029pc09",
    "hg029pc48", "hg075pc20", "hg206pc36", "hg206pc34", "hg206pc35",
    "hg206pc32", "hg206pc33", "hg206pc30", "hg206pc31", "hg075pc29",
    "hg029pc41", "cz0068pc01", "cz0307pc01", "cz0071pc01", "cz0065pc01",
    "cz0310pc01", "cz0086pc01", "cz0304pc01", "cz0308pc01", "cz0303pc01",
    "cz0062pc01"]


def send(data, host, port):
    c = httplib.HTTPConnection(host, port)
    c.request("POST", "/push", json.dumps(data))
    r = c.getresponse()
    print r.status, r.read()

def main(host, port):
    bits = {}
    for pc in PCS:
        bits[pc] = {'status': 'offline'}
    data = {'datasource': 'test',
            'data': bits}
    send(data, host, port)
    while True:
        data = {'datasource': 'test',
                'data': {random.choice(PCS):
                             random.choice(STATI)}}
        send(data, host, port)
        time.sleep(0.1)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.argv.append('localhost')
    if len(sys.argv) == 2:
        sys.argv.append('1235')
    main(sys.argv[1], int(sys.argv[2]))
