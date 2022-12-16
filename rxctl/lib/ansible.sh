#!/bin/bash -e

FACTS="~/.cache/rx/ansible/facts.json"

do_facts(){
__run <<EOF
if [ ! -s $FACTS ] ; then
    exit 0
fi
SYSAGE=\$(awk '{print int(0.5 + \$1)}' /proc/uptime)
FACTAGE=\$(( \$(date +"%s") - \$(stat -c'%W' $FACTS) ))
if [ \$FACTAGE -gt \$SYSAGE ] ; then
    exit 0
fi
exit 1
EOF
}

bootstrap(){
    if ! __run python3 -V >/dev/null 2>&1 ; then
        __log.error __ansible: bootstrap: Python3 not available
        exit 1
    fi
    CDIR=$(pwd)
    cd $(dirname $RX_ANSIBLE)
    LAV=$(python3 -c "from ansible.release import __version__ ; print(__version__)")
    SRC_TAR="${RX_CACHE}/ansible-${LAV}.tar.gz"
    if [ ! -f "${SRC_TAR}" ] ; then
        __log.info __ansible: bootstrap: Pack ansible $LAV
        mkdir -p ${RX_CACHE}
        rm -fv ${RX_CACHE}/ansible-*.tar.gz
        tar -czf $SRC_TAR --exclude=*.pyc --exclude=__pycache__ ansible/release.py ansible/modules ansible/module_utils
    else
        __log.debug __ansible: bootstrap: Local ansible version: $LAV
    fi
    cd $CDIR
    RAV=$(__run <<EOF
    mkdir -p ~/.cache/rx
    cd ~/.cache/rx
    python3 -c "from ansible.release import __version__ ; print(__version__)" 2>/dev/null
EOF
) || true
    __log.debug __ansible: bootstrap: Remote ansible version: $RAV
    if [ "$LAV" != "$RAV" ] ; then
        __log.info __ansible: bootstrap: Pushing ansible $LAV
        __put $SRC_TAR /tmp/ansible.tar.gz
        __run <<EOF
        cd ~/.cache/rx
        rm -rf ansible
        tar -xzf /tmp/ansible.tar.gz
EOF
    fi   
    if do_facts ; then
        __log.info __ansible: bootstrap: Facts
        module setup --gather_subset="distribution,pkg_mgr,service_mgr,virtual" | jq -arM '.ansible_facts' | __run "rm -f ${FACTS} ; cat >${FACTS}"
    fi
}

args2json(){
    __log.debug __ansible: args2json: raw: $@
    ARGS='{\"ANSIBLE_MODULE_ARGS\":{'
    STRIP=0
    for A in $@ ; do
        echo $A | grep -qE '^--[^ =]+=[^=]+$' || __log.error __ansible: args2json: Invalid argument: $A
        STRIP=1
        read K V < <(echo $A | sed -r 's/^--(.+)=(.+)$/\1 \2/g')
        ARGS=${ARGS}'\"'$K'\"':'\"'$V'\",'
    done
    if [ $STRIP -eq 1 ] ; then 
        ARGS=${ARGS::-1}
    fi
    ARGS=${ARGS}'}}'
    __log.debug __ansible: args2json: json: $ARGS
    echo $ARGS
}

check(){
    [ -n "$1" ] && ! echo $1 | grep -qE '^--[a-z]'
}

module(){
    MODULE=$1
    shift
    ARGS="$(args2json $@)"
    __log.debug __ansible: module raw: $MODULE $ARGS
    R=$(__run "cd ~/.cache/rx ; python3 -m ansible.modules.${MODULE} ${ARGS}" | jq 'del(.invocation)' | jq 'del(.diff)')
    FAILED=$(echo $R | jq -r '.failed')
    if [ "${FAILED}" = "true" ] ; then
        echo $R >&2
        return 1
    fi
    echo $R
}


if [ $RX_LOG_VERBOSITY -ge 2 ] ; then
    set -x
fi

if [ -z "$RX_ANSIBLE_BOOTSTRAPED" ] ; then
    bootstrap
fi
export RX_ANSIBLE_BOOTSTRAPED=yes

CMD=$(echo $0 | awk -F'.' '{print $2}')

case $CMD in
    setup)
        __log.debug __ansible: cmd: setup
        if check "$1" ; then
            __ansible setup --gather_subset="!all,!min,${1}" | jq '.ansible_facts'
        else
            __ansible setup | jq '.ansible_facts'
        fi
    ;;
    fact)
        __log.debug __ansible: cmd: fact
        __run "cat ${FACTS}" | jq -r '."'$1'"'
    ;;
    package)
        __log.debug __ansible: cmd: package
        MGR=$(__ansible.fact ansible_pkg_mgr)
        if check "$1" ; then
            NAME="$1"
            shift
        fi
        if [ -n "$NAME" ] ; then
            __ansible $MGR --name="$NAME" "$@" 
        else
            __ansible $MGR "$@" 
        fi
    ;;
    service)
        __log.debug __ansible: cmd: service
        MGR=$(__ansible.fact ansible_service_mgr)
        if check "$1" ; then
            NAME="$1"
            shift
        fi
        if [ -n "$NAME" ] ; then
            __ansible $MGR --name="$NAME" "$@" | jq 'del(.status)'
        else
            __ansible $MGR "$@" | jq 'del(.status)'
        fi
    ;;
    *)
        MODULE=$1
        shift
        __log.info __ansible: module : $MODULE $@
        module $MODULE "$@"
    ;;
esac
