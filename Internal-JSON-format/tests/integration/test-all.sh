#!/usr/bin/env bash
set -Eeuo pipefail

DIR="$(dirname "${BASH_SOURCE[0]}")"
ITEM_SCHEMA="${ITEM_SCHEMA:-$DIR/../../schemas/item.json}"
ITEM_JSON_DIR="${ITEM_JSON_DIR:-}"
ITEM_SCHEMA_PATCH="${ITEM_SCHEMA_PATCH:-$DIR/allow-minor-deviations.patch.json}"

if [[ "$ITEM_JSON_DIR" == "" || ! -d "$ITEM_JSON_DIR" ]] ; then
    echo "Error: \$ITEM_JSON_DIR is not a directory: $ITEM_JSON_DIR"
    echo 'Set the ITEM_JSON_DIR envar to the directory containing JSON to test'
    exit 1
fi

if [[ "$ITEM_SCHEMA_PATCH" != "" ]] ; then
    VALIDATION_SCHEMA="$(mktemp)"
    poetry run jsonpatch --indent 2 "$ITEM_SCHEMA" "$ITEM_SCHEMA_PATCH" > "$VALIDATION_SCHEMA"
    echo "Validating with $ITEM_SCHEMA patched with $ITEM_SCHEMA_PATCH as $VALIDATION_SCHEMA to allow known data errors" 1>&2
else
    echo "Validating with $ITEM_SCHEMA (unmodified)." 1>&2
    VALIDATION_SCHEMA="$ITEM_SCHEMA"
fi

find "$ITEM_JSON_DIR" -type f -name '*.json' \
    | env SHELL=/bin/sh parallel -X ajv test --json-pointers --verbose -s "$VALIDATION_SCHEMA" "-d={}" --valid 2>&1 \
    | grep -vP 'passed test$'
