#!/bin/sh
now=`date`
oldsum=`cksum sha256.txt`
sha256sum *.py > sha256.txt
newsum=`cksum sha256.txt`
if [ "$oldsum" != "$newsum" ]; then
    echo $now: changes detected in pico/scripts
fi;
cd utils
oldsum=`cksum sha256.txt`
sha256sum *.py > sha256.txt
newsum=`cksum sha256.txt`
if [ "$oldsum" != "$newsum" ]; then
    echo $now: changes detected in pico/scripts/utils
fi;
cd ../lib
oldsum=`cksum sha256.txt`
sha256sum *.py > sha256.txt
newsum=`cksum sha256.txt`
if [ "$oldsum" != "$newsum" ]; then
    echo $now: changes detected in pico/scripts/lib
fi;

