#!/bin/bash

# Script powersaves the display every 20 seconds. Useful if a proper screensaver or power management isn't active for the current system.
# Parameter 1 is the delay to start the sleep cycle. Parameter 2 is the gap between setting the displays off when inside the loop.

# Test if input is positive.
function is_positive_int {
    test -n "$1" -a "$1" -ge 0 2>/dev/null;
}

is_positive_int "$1" && TIMEOUT_INIT="$1" || TIMEOUT_INIT=5
is_positive_int "$2" && TIMEOUT_CONTINUOUS="$2" || TIMEOUT_CONTINUOUS=20

set -eu

sleep "${TIMEOUT_INIT}s"
while true; do
	xset dpms force off
	sleep "${TIMEOUT_CONTINUOUS}s"
done
