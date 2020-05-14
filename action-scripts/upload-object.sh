#!/bin/env sh
./s3-rest  -m put -b $2 -k $3 \
           -c $1 -p $4 -f \
           -t "partNumber=$5;uploadId=$6" -H "ETag"