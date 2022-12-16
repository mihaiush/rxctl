#!/bin/bash 

set -e 
set -o pipefail

if [ $RX_LOG_VERBOSITY -ge 2 ] ; then
    set -x
fi

NA=$(( $# - 2 ))
ARGS=""
while [ $NA -gt 0 ] ; do
    ARGS="${ARGS} ${1}"
    shift
    NA=$(( $NA - 1 ))
done

CMD=$(basename $0)

if [ "$CMD" = "__put" ] ; then
    SRC="${1}"
    DST=${RX_HOST}:"${2}"
elif [ "$CMD" = "__get" ] ; then
    SRC=${RX_HOST}:"${1}"
    DST="${2}"
else
    exit 1
fi

__log.debug "${CMD}${ARGS}: '${SRC}' -> '${DST}'"
${RX_SCP_CMD}${ARGS} "${SRC}" "${DST}"
