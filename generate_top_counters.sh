#!/bin/bash
cd /home/zen/zenofewords/
source /home/zen/.virtualenvs/zenofewords/bin/activate
source .env
python manage.py pgo_generate_top_counters
