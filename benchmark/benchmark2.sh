#!/usr/bin/env bash
set -u

ITERATIONS="${ITERATIONS:-100}"
REBUILD_WAIT="${REBUILD_WAIT:-180}"
RUN_TIMEOUT="${RUN_TIMEOUT:-120s}"
FLAG='flag{stochastic_parrot}'

if ! [[ "$ITERATIONS" =~ ^[1-9][0-9]*$ ]]; then
  printf 'ITERATIONS must be a positive integer, got: %s\n' "$ITERATIONS" >&2
  exit 2
fi

pwn_success=0
pwn_failure=0
false_positive_success=0
false_positive_failure=0
false_negative_success=0
false_negative_failure=0

for ((iteration = 1; iteration <= ITERATIONS; iteration++)); do
  printf 'iteration=%s/%s\n' "$iteration" "$ITERATIONS"

  printf 'case=pwn-script rebuild\n'
  if docker compose -f ../docker-compose.yml --progress quiet up -d --force-recreate --wait --wait-timeout "$REBUILD_WAIT" > /dev/null; then
    printf 'case=pwn-script run\n'
    output="$(timeout --kill-after=5s "$RUN_TIMEOUT" ../pwn-script.sh 2>&1)"
    if grep -Fq "$FLAG" <<<"$output"; then
      pwn_success=$((pwn_success + 1))
      printf 'case=pwn-script result=success\n'
    else
      pwn_failure=$((pwn_failure + 1))
      printf 'case=pwn-script result=failure\n'
    fi
  else
    pwn_failure=$((pwn_failure + 1))
    printf 'case=pwn-script result=failure rebuild_failed\n'
  fi

  printf 'case=false-positive rebuild\n'
  if docker compose -f ../docker-compose.yml --progress quiet up -d --force-recreate --wait --wait-timeout "$REBUILD_WAIT" > /dev/null; then
    printf 'case=false-positive run\n'
    output="$(timeout --kill-after=5s "$RUN_TIMEOUT" ./false-positive.sh 2>&1)"
    if grep -Fq "$FLAG" <<<"$output"; then
      false_positive_success=$((false_positive_success + 1))
      printf 'case=false-positive result=success\n'
    else
      false_positive_failure=$((false_positive_failure + 1))
      printf 'case=false-positive result=failure\n'
    fi
  else
    false_positive_failure=$((false_positive_failure + 1))
    printf 'case=false-positive result=failure rebuild_failed\n'
  fi

  printf 'case=false-negative rebuild\n'
  if docker compose -f ../docker-compose.yml --progress quiet up -d --force-recreate --wait --wait-timeout "$REBUILD_WAIT" > /dev/null; then
    printf 'case=false-negative run\n'
    output="$(timeout --kill-after=5s "$RUN_TIMEOUT" ./false-negative.sh 2>&1)"
    if grep -Fq "$FLAG" <<<"$output"; then
      false_negative_failure=$((false_negative_failure + 1))
      printf 'case=false-negative result=failure\n'
    else
      false_negative_success=$((false_negative_success + 1))
      printf 'case=false-negative result=success\n'
    fi
  else
    false_negative_failure=$((false_negative_failure + 1))
    printf 'case=false-negative result=failure rebuild_failed\n'
  fi
done

printf 'case\tno_success\tno_failure\t%%success\n'
printf 'pwn-script\t%s\t%s\t%s\n' \
  "$pwn_success" "$pwn_failure" "$((pwn_success * 100 / ITERATIONS))"
printf 'false-positive\t%s\t%s\t%s\n' \
  "$false_positive_success" "$false_positive_failure" "$((false_positive_success * 100 / ITERATIONS))"
printf 'false-negative\t%s\t%s\t%s\n' \
  "$false_negative_success" "$false_negative_failure" "$((false_negative_success * 100 / ITERATIONS))"
