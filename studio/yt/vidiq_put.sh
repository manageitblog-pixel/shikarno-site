#!/bin/sh
# Завантаження локального відео у сховище vidIQ (резюмоване) за підписаним URL з vidiq_video_upload(localFile).
# usage: sh studio/yt/vidiq_put.sh <file> <bytes> <signed_url> <uploadId>
set -u; F="$1"; N="$2"; U="$3"; ID="$4"; T=video/mp4
fail() { printf "vidIQ upload stopped: %s\n" "$*" >&2; exit 1; }
c() { curl -q -sS -g --connect-timeout 30 "$@"; }
code() { tr -d "\r" | sed -n "s/^HTTP\/[0-9.]* \([0-9][0-9][0-9]\).*/\1/p" | tail -n 1; }
hdr() { tr -d "\r" | grep -i "^$1:" | tail -n 1 | sed "s/^[^:]*: *//"; }
R=$(c -m 60 -o /dev/null -D - -X POST -H "x-goog-resumable: start" -H "x-upload-content-type: $T" -H "x-upload-content-length: $N" -H "Content-Length: 0" "$U") || fail "no storage"
X=$(printf "%s\n" "$R" | hdr location); [ -n "$X" ] || fail "refused (link expired?)"
Q=$(c -m 60 -o /dev/null -D - -X PUT -H "Content-Length: 0" -H "Content-Range: bytes */$N" "$X") || fail lost
case "$(printf "%s\n" "$Q" | code)" in
 200|201) ;;
 308) R=$(printf "%s\n" "$Q" | hdr range | sed "s/.*-//"); O=$(( ${R:--1} + 1 ))
      W=$(c -Y 1 -y 120 -o /dev/null -w "%{http_code}" -X PUT -C "$O" -T "$F" "$X"); case "$W" in 200|201) ;; *) fail "interrupted $W";; esac ;;
 *) fail unexpected ;;
esac
echo "vidIQ upload complete $ID"
