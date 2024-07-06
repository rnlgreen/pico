#!/bin/sh
now=`date`
here=`pwd`
echo $now
for i in $(find . -type d);
do
    cd $here/$i
    oldsum=`cksum sha256.txt`
    sha256sum *.py *.mpy > sha256.txt 2>/dev/null
    newsum=`cksum sha256.txt`
    if [ "$oldsum" != "$newsum" ]; then
        echo changes detected in $here/$i
    else
        echo no changes detected in $here/$i
    fi;
done
