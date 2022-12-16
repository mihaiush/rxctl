#!/bin/bash 

set -e 
set -o pipefail

if [ $RX_LOG_VERBOSITY -ge 2 ] ; then
    set -x
fi

if [ "${1}" = "-r" ] ; then
    R="-r "
    shift
else
    R=""
fi

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

__log.debug "$CMD: '${SRC}' -> '${DST}'"
${RX_SCP_CMD} ${R}"${SRC}" "${DST}"
