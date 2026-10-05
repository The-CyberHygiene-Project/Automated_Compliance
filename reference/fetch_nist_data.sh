#!/bin/bash
# Download NIST's public data files used to build the Rev 3 kit and the Rev 2 to Rev 3 mapping.
cd "$(dirname "$0")" || exit 1
curl -fsSL -o NIST_SP800-171_rev3_catalog.json \
  https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-171/rev3/json/NIST_SP800-171_rev3_catalog.json
curl -fsSL -o sp800-171r2-to-r3-analysis.xlsx \
  https://csrc.nist.gov/files/pubs/sp/800/171/r3/final/docs/sp800-171r2-to-r3-analysis.xlsx
ls -l NIST_SP800-171_rev3_catalog.json sp800-171r2-to-r3-analysis.xlsx
