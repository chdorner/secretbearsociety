#!/usr/bin/env python

import os

import requests


def fetch_peer_blocks():
    peers_f = open('data/blocklist-peers', 'r')
    peers = [p.strip() for p in peers_f.readlines()]

    all_blocks = {}
    for peer in peers:
        r = requests.get(f'https://{peer}/api/v1/instance/domain_blocks')
        r.raise_for_status()
        blocks = [b for b in r.json() if '*' not in b['domain']]

        for block in blocks:
            comment = block['comment']
            all_blocks[block['domain']] = {
                'domain': block['domain'],
                'comment': f'Imported from {peer}: {comment}'
            }

    return all_blocks


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


def load_blocklist():
    blocklist_f = open('data/blocklist', 'r')
    return {
        h.strip(): {'domain': h.strip(), 'comment': ''}
        for h in blocklist_f.readlines()
    }


def load_allowlist():
    allowlist_f = open('data/allowlist', 'r')
    return {h.strip() for h in allowlist_f.readlines()}


def create_blocks(blocks):
    for block in blocks:
        domain = block['domain']
        body = {
            'domain': domain,
            'severity': 'suspend',
        }
        if block['comment']:
            body['public_comment'] = block['comment']

        r = requests.post(f'https://{host}/api/v1/admin/domain_blocks', headers={'Authorization': auth}, json=body)
        if r.status_code == 422 and r.json().get('existing_domain_block'):
            continue
        r.raise_for_status()
        print(f'blocked {domain}')


def remove_blocks(blocks):
    for block in blocks:
        id_ = block['id']
        domain = block['domain']
        r = requests.delete(f'https://{host}/api/v1/admin/domain_blocks/{id_}', headers={'Authorization': auth})
        r.raise_for_status()
        print(f'unblocked {domain}')

if __name__ == '__main__':
    host = os.environ['MASTODON_HOST']
    token = os.environ['MASTODON_TOKEN']
    auth = f'Bearer {token}'

    allowlist = load_allowlist()
    new_blocks = {**load_blocklist(), **fetch_peer_blocks()}
    existing_blocks = existing_blocked_domains(host, auth)

    create = new_blocks.keys() - existing_blocks.keys() - allowlist
    remove = allowlist.intersection(existing_blocks.keys()).union(existing_blocks.keys() - new_blocks.keys())

    create_blocks([v for (k, v) in new_blocks.items() if k in create])
    remove_blocks([v for (k, v) in existing_blocks.items() if k in remove])
