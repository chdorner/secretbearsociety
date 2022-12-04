#!/usr/bin/env python

import json
import os

import requests


def fetch_rapidblock_blocks():
    r = requests.get('https://rapidblock.org/blocklist.json')
    r.raise_for_status()
    return {
        k: {
            'domain': k,
            'public_comment': compile_comment(v),
            'severity': 'suspend' if v['isBlocked'] else 'silence',
        }
        for k, v in r.json()['blocks'].items()
        if v['isBlocked'] is True
    }


def fetch_peer_blocks():
    peers_f = open('data/blocklist-peers', 'r')
    peers = [p.strip() for p in peers_f.readlines()]

    all_blocks = {}
    for peer in peers:
        r = requests.get(f'https://{peer}/api/v1/instance/domain_blocks')
        r.raise_for_status()
        blocks = [b for b in r.json() if '*' not in b['domain']]

        for block in blocks:
            all_blocks[block['domain']] = {
                'domain': block['domain'],
                'public_comment': block['comment'],
                'severity': block['severity'],
            }

    return all_blocks


def load_blocklist():
    with open('data/blocklist.json') as file:
        blocklist = json.load(file)
        return {
            k: {
                'domain': k,
                'public_comment': compile_comment(v),
                'severity': 'suspend' if v['isBlocked'] is True else 'silence',
            }
            for k, v in blocklist['blocks'].items()
        }
    return {}


def compile_comment(block):
    comment = ''
    if block.get('reason'):
        comment += block['reason'] + ': '
    comment += ', '.join(block.get('tags', []))
    return comment


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


def load_allowlist():
    allowlist_f = open('data/allowlist', 'r')
    return {h.strip() for h in allowlist_f.readlines()}


def create_blocks(blocks):
    for block in blocks:
        domain = block['domain']
        r = requests.post(f'https://{host}/api/v1/admin/domain_blocks', headers={'Authorization': auth}, json=block)
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

def update_blocks(existing, new):
    for domain, block_e in existing.items():
        block_n = new.get(domain, None)
        if block_n is None:
            continue

        if block_e['public_comment'] != block_n['public_comment'] or \
            block_e['severity'] != block_n['severity']:

            id_ = block_e['id']
            r = requests.put(f'https://{host}/api/v1/admin/domain_blocks/{id_}', headers={'Authorization': auth}, json=block_n)
            r.raise_for_status()
            print(f'updated block for {domain}')



if __name__ == '__main__':
    host = os.environ['MASTODON_HOST']
    token = os.environ['MASTODON_TOKEN']
    auth = f'Bearer {token}'

    allowlist = load_allowlist()
    new_blocks = {**fetch_peer_blocks(), **fetch_rapidblock_blocks(), **load_blocklist()}
    existing_blocks = existing_blocked_domains(host, auth)

    create = new_blocks.keys() - existing_blocks.keys() - allowlist
    remove = allowlist.intersection(existing_blocks.keys()).union(existing_blocks.keys() - new_blocks.keys())

    create_blocks([v for (k, v) in new_blocks.items() if k in create])
    remove_blocks([v for (k, v) in existing_blocks.items() if k in remove])
    update_blocks(existing_blocks, new_blocks)
