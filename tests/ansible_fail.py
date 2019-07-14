#!/usr/bin/env python

import sys
import json

message = """WARNING: You are trying to run unfit playbooks in automated testing.
"""
sys.stdout.write(json.dumps({'failed': True, 'stdout': message}))
sys.stdout.write('\n')
