#!/bin/bash -x

OFFERING=${1}
PLAN=${2}

if [ -z ${OFFERING} ] || [ -z ${PLAN} ]; then
        echo "TAP CLI must be available in current directory and already logged in."
        echo "Help: ./check_capacity.sh <OFFERING> <PLAN>"
        exit 1
fi

echo "Checking capacity of environment"

function clean {
        ./tap svcs | grep "instance" | grep "RUNNING" | cut -d ' ' -f 2 | xargs -n 1 ./tap service-stop
        sleep 5
        ./tap svcs | grep "instance" | cut -d ' ' -f 2 | xargs -n 1 ./tap ds
}

for i in {1..250}
do
        ./tap cs "${OFFERING}" "${PLAN}" "${OFFERING}-instance${i}"
        while true; do
                STATE=$(./tap svcs | grep "${OFFERING}-instance${i}" | cut -d '|' -f 5 | sed 's/^ *//;s/ *$//')
                if [ "${STATE}" = "RUNNING" ]; then
                        break
                fi
                if [ "${STATE}" = "STOPPED" ]; then
                        echo "${i}th instance of ${OFFERING} could not fit into the environment. See reason:"
                        ./tap s "${OFFERING}-instance${i}"
                        clean
                        exit 0
                fi

                if [ "${STATE}" = "FAILURE" ]; then
                        echo "${i}th instance of ${OFFERING} failed to start. See reason:"
                        ./tap s "${OFFERING}-instance${i}"
                        clean
                        exit 0
                fi
        done
done
