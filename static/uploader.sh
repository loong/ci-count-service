#!/bin/bash

DIR=$1

if [ ! -d "$DIR" ] && [ ! -f "$DIR" ]; then
    echo "$DIR not found";
    exit 1;
fi

echo $DIR
zip -r src.zip $DIR

curl -F file=@src.zip https://clear-ci.herokuapp.com/upload

