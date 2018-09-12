#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


'//anaconda/envs/aiida_v12/bin/mock_runcry17' 'main'   
