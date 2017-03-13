#!/bin/bash
./manage.py pgo_master_import
./manage.py pgo_stats_import
./manage.py pgo_calculate_cp
./manage.py pgo_calculate_move_stats
