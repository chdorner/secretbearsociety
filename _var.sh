#!/usr/bin/env sh

if [ -z $MASTODON_SERVER ]; then
  echo "MASTODON_SERVER is missing!"
  exit 1
fi

if [ -z $MASTODON_TOKEN ]; then
  echo "MASTODON_TOKEN is missing!"
  echo "try running ./authorize to obtain a new token."
  exit 1
fi
