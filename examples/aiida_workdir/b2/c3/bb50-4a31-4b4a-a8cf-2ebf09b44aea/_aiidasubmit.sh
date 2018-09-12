#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


'/usr/local/bin/runcry17' 'main'   
