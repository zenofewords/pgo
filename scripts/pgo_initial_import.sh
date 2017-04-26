#!/bin/bash
if (( $# != 1 ))
then
    echo "Path to import file is required"
    exit 1
fi

./manage.py pgo_master_import $1
