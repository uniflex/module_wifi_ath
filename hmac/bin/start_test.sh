#!/bin/bash

echo "Standalone hybrid MAC test ... "

sudo ./hybrid_tdma_csmaac -d 0 -i wifi0 -f 20000 -n 10
