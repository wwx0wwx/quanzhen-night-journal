#!/usr/bin/env bash
set -euo pipefail
cd /opt/blog-src
/usr/bin/env python3 /opt/blog-src/scripts/generate_night_journal.py >> /opt/blog-src/logs/night-journal.log 2>&1
