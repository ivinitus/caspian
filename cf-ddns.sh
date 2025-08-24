#!/bin/bash
IP=$(curl -s https://api.ipify.org)
ZONE_ID="7734da89695f1e12a95d26539eb2ba30"
RECORD_ID="a729289c3ccf7ff2a3ebaf403a23c66b"
TOKEN="qeFCncbFB0dZOAdBCkPaVUeG_C17FtgozZuE-jdc"

curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     --data "{\"type\":\"A\",\"name\":\"vinitus.online\",\"content\":\"$IP\",\"ttl\":1,\"proxied\":false}"

