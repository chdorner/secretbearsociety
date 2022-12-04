#!/usr/bin/env python

import json
import os

import requests


def existing_blocked_domains(host, auth):
    blocked_domains = {}
    url = f'https://{host}/api/v1/admin/domain_blocks'
    while True:
        r = requests.get(url, headers={'Authorization': auth})
        r.raise_for_status()
        blocked_domains = {**blocked_domains, **{b['domain']: b for b in r.json()}}
        if 'next' in r.links:
            url = r.links['next']['url']
        else:
            break

    return blocked_domains

def remove_blocks(blocks):
    for _, block in blocks.items():
        id_ = block['id']
        domain = block['domain']
        r = requests.delete(f'https://{host}/api/v1/admin/domain_blocks/{id_}', headers={'Authorization': auth})
        r.raise_for_status()
        print(f'unblocked {domain}')

if __name__ == '__main__':
    host = os.environ['MASTODON_HOST']
    token = os.environ['MASTODON_TOKEN']
    auth = f'Bearer {token}'

    existing_blocks = existing_blocked_domains(host, auth)
    remove_blocks(existing_blocks)
