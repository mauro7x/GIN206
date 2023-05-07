#!/bin/sh

site="${SITE:-grenoble}"

echo "Flashing border-router..."
iotlab-node --flash ./border-router/border-router.iotlab-m3 -l $site,m3,$1

echo "Flashing resource-server..."
iotlab-node --flash ./resource-server.iotlab-m3 -l $site,m3,$2

echo "Done!"
