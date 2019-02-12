#!/bin/sh
# Build the lambda deploy
function build_app() {
  o="../builds/app.zip"
  [ -f "$o" ] && rm "$o"
  zip -X -r $o *.py
}

# Build the mutagen layer
function build_mutagen() {
  MUTAGEN_VERSION=1.42.0
  d=$(mktemp -d)
  c=$(pwd)
  mkdir -p $d/python/lib/python3.7/site-packages/
  wget -cO "mutagen-$MUTAGEN_VERSION.zip" "https://github.com/quodlibet/mutagen/archive/release-$MUTAGEN_VERSION.zip"
  unzip "mutagen-$MUTAGEN_VERSION.zip"
  rm "mutagen-$MUTAGEN_VERSION.zip"
  mv mutagen-release-$MUTAGEN_VERSION/* $d/python/lib/python3.7/site-packages/
  rm -rf mutagen-release-$MUTAGEN_VERSION
  cd $d
  # The find (with the zip -X) makes the zip reproducible
  # Relies on the files being read in the same order. I assume this to be the case
  find python -exec touch -t 201901010000 {} +
  zip -X -r mutagen-$MUTAGEN_VERSION.zip python
  touch -t 201901010000 mutagen-$MUTAGEN_VERSION.zip +
  cp mutagen-$MUTAGEN_VERSION.zip $c/../builds/
  rm -rf $d
}

[ -z $1 ] && t="app" || t=$1
build_$t