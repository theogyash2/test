#!/usr/bin/env python3
import sys
import json
import boto3

instance_id = sys.argv[1]
missing = sys.argv[2].split(',')

ssm = boto3.client('ssm', region_name='ap-south-1')

# Load setup commands
with open('setup_commands.json') as f:
    setup = json.load(f)

# Build install commands
commands = []
for item in missing:
    if item in setup['requirements']:
        commands.append(setup['requirements'][item]['install'])
    elif item in setup['services']:
        commands.append(setup['services'][item]['install'])

# Execute
if commands:
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunPowerShellScript',
        Parameters={'commands': commands}
    )