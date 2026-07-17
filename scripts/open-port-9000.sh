#!/bin/bash
set -e
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
MACS=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/network/interfaces/macs/ | head -1 | tr -d '/')
SG_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/network/interfaces/macs/${MACS}/security-group-ids")
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region)
echo "SG: $SG_ID, Region: $REGION"
if ! command -v aws &>/dev/null; then
  sudo apt-get update -qq && sudo apt-get install -y -qq awscli 2>/dev/null
fi
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 9000 --cidr 0.0.0.0/0 --region "$REGION" 2>&1
echo "Done"
