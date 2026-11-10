#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
#
# Collect OpenSCAP CUI Scan Results — Centralized Reporting
# CyberHygiene Project — NIST 800-171 Compliance
#
# Collects the most recent HTML reports and XML results from all CPN systems
# to dc1, then generates a consolidated Markdown summary and an HTML dashboard
# served at https://dc1.[DOMAIN.ORG]/dashboard/openscap-dashboard.html
#
# Usage:
#   collect_openscap_results.sh [--collect-only | --scan-and-collect]
#
# Modes:
#   --collect-only       (default) Fetch latest results without triggering scans
#   --scan-and-collect   Trigger fresh scans first, wait, then collect
#

set -euo pipefail

# --- Configuration -----------------------------------------------------------
WORKSTATIONS="ws-a ws-b ws-c"
ALL_HOSTS="dc1 ws-a ws-b ws-c"
SCAN_SCRIPT="/usr/local/bin/openscap_cui_scan.sh"
REMOTE_RESULTS_DIR="/var/log/openscap"
OUTPUT_DIR="/home/[USERNAME]/CyberSecurity/Current/Assessments/OpenSCAP"
WEB_DIR="/var/www/internal-dashboards"
WEB_REPORTS_DIR="${WEB_DIR}/openscap"
TODAY=$(date +%Y%m%d)
TODAY_PRETTY=$(date +%Y-%m-%d)
SCAN_TIMEOUT=600  # 10 minutes max per scan
COLLECT_TIMEOUT=60
TMP_DIR=$(mktemp -d /tmp/openscap-collect.XXXXXX)
trap 'rm -rf "${TMP_DIR}"' EXIT
SSH_USER="[USERNAME]"
SSH_KEY="/home/[USERNAME]/.ssh/id_ecdsa"
SSH_OPTS="-o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes -i ${SSH_KEY}"

# --- Functions ---------------------------------------------------------------
log() { echo "[$(date '+%H:%M:%S')] $*"; }
warn() { echo "[$(date '+%H:%M:%S')] WARNING: $*" >&2; }
err()  { echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2; }

ssh_cmd() {
    local host="$1"; shift
    ssh ${SSH_OPTS} "${SSH_USER}@${host}.[DOMAIN.ORG]" "$@"
}

# Get the most recent file matching a glob pattern on a remote host
# Returns the full path of the newest file
get_latest_remote() {
    local host="$1" pattern="$2"
    ssh_cmd "${host}" "sudo ls -t ${REMOTE_RESULTS_DIR}/${pattern} 2>/dev/null | head -1"
}

get_latest_local() {
    local pattern="$1"
    ls -t ${REMOTE_RESULTS_DIR}/${pattern} 2>/dev/null | head -1
}

# --- Trigger scans (--scan-and-collect only) ---------------------------------
trigger_scans() {
    log "Triggering fresh scans on all systems..."

    # Local scan on dc1
    log "[dc1] Starting local scan..."
    if [[ -x "${SCAN_SCRIPT}" ]]; then
        ${SCAN_SCRIPT} &
        local dc1_pid=$!
    else
        warn "[dc1] Scan script not found at ${SCAN_SCRIPT}"
        local dc1_pid=""
    fi

    # Remote scans on workstations
    local pids=()
    for ws in ${WORKSTATIONS}; do
        log "[${ws}] Triggering remote scan..."
        if ssh_cmd "${ws}" "sudo test -x ${SCAN_SCRIPT}" 2>/dev/null; then
            ssh_cmd "${ws}" "sudo ${SCAN_SCRIPT}" &
            pids+=($!)
            log "[${ws}] Scan started (PID $!)."
        else
            warn "[${ws}] Cannot connect or scan script not found."
        fi
    done

    # Wait for all scans with timeout
    log "Waiting for scans to complete (timeout: ${SCAN_TIMEOUT}s)..."
    local start_time=$(date +%s)
    local all_pids=("${dc1_pid}" "${pids[@]}")
    for pid in "${all_pids[@]}"; do
        [[ -z "$pid" ]] && continue
        local elapsed=$(( $(date +%s) - start_time ))
        local remaining=$(( SCAN_TIMEOUT - elapsed ))
        if [[ $remaining -le 0 ]]; then
            warn "Scan timeout reached, proceeding with collection."
            break
        fi
        # Wait with a simple check loop
        while kill -0 "$pid" 2>/dev/null; do
            elapsed=$(( $(date +%s) - start_time ))
            if [[ $elapsed -ge $SCAN_TIMEOUT ]]; then
                warn "Scan timeout reached (PID ${pid} still running)."
                break 2
            fi
            sleep 5
        done
    done
    log "Scan phase complete."
    echo ""
}

# --- Collect results ---------------------------------------------------------
collect_results() {
    log "Collecting results from all systems..."
    mkdir -p "${OUTPUT_DIR}"

    local collected=0

    for host in ${ALL_HOSTS}; do
        log "[${host}] Collecting..."

        local report_dest="${OUTPUT_DIR}/cui_report_${host}_${TODAY}.html"
        local xml_dest="${TMP_DIR}/cui_results_${host}.xml"

        if [[ "${host}" == "dc1" ]]; then
            # Local collection
            local latest_report latest_xml
            latest_report=$(get_latest_local "cui_report_dc1_*.html")
            latest_xml=$(get_latest_local "cui_results_dc1_*.xml")

            if [[ -n "${latest_report}" && -f "${latest_report}" ]]; then
                cp "${latest_report}" "${report_dest}"
                log "[dc1] HTML report: $(basename "${latest_report}") -> $(basename "${report_dest}")"
            else
                warn "[dc1] No HTML report found in ${REMOTE_RESULTS_DIR}/"
            fi

            if [[ -n "${latest_xml}" && -f "${latest_xml}" ]]; then
                cp "${latest_xml}" "${xml_dest}"
                log "[dc1] XML results copied for parsing."
                collected=$((collected + 1))
            else
                warn "[dc1] No XML results found in ${REMOTE_RESULTS_DIR}/"
            fi
        else
            # Remote collection via SCP
            local latest_report latest_xml
            latest_report=$(get_latest_remote "${host}" "cui_report_${host}_*.html" 2>/dev/null) || true
            latest_xml=$(get_latest_remote "${host}" "cui_results_${host}_*.xml" 2>/dev/null) || true

            if [[ -n "${latest_report}" ]]; then
                if ssh ${SSH_OPTS} -o ConnectTimeout=${COLLECT_TIMEOUT} \
                    "${SSH_USER}@${host}.[DOMAIN.ORG]" \
                    "sudo cat '${latest_report}'" > "${report_dest}" 2>/dev/null; then
                    log "[${host}] HTML report: $(basename "${latest_report}") -> $(basename "${report_dest}")"
                else
                    warn "[${host}] Failed to fetch HTML report."
                    rm -f "${report_dest}"
                fi
            else
                warn "[${host}] No HTML report found."
            fi

            if [[ -n "${latest_xml}" ]]; then
                if ssh ${SSH_OPTS} -o ConnectTimeout=${COLLECT_TIMEOUT} \
                    "${SSH_USER}@${host}.[DOMAIN.ORG]" \
                    "sudo cat '${latest_xml}'" > "${xml_dest}" 2>/dev/null; then
                    log "[${host}] XML results copied for parsing."
                    collected=$((collected + 1))
                else
                    warn "[${host}] Failed to fetch XML results."
                    rm -f "${xml_dest}"
                fi
            else
                warn "[${host}] No XML results found."
            fi
        fi
    done

    echo ""
    log "Collected XML results from ${collected} system(s)."
    return 0
}

# --- Parse XML results into temp files ----------------------------------------
parse_results() {
    log "Parsing XML results..."

    # Arrays for score summary table
    declare -gA host_pass host_fail host_na host_score

    for host in ${ALL_HOSTS}; do
        local xml_file="${TMP_DIR}/cui_results_${host}.xml"
        if [[ ! -f "${xml_file}" ]]; then
            warn "[${host}] No XML results available, skipping."
            host_pass[${host}]="—"
            host_fail[${host}]="—"
            host_na[${host}]="—"
            host_score[${host}]="—"
            continue
        fi

        # Count pass/fail/notapplicable
        # grep -c outputs "0" AND exits 1 when no match; || true prevents set -e abort
        local pass_count fail_count na_count
        pass_count=$(grep -c '<result>pass</result>' "${xml_file}" || true)
        fail_count=$(grep -c '<result>fail</result>' "${xml_file}" || true)
        na_count=$(grep -c '<result>notapplicable</result>' "${xml_file}" || true)
        pass_count=${pass_count:-0}
        fail_count=${fail_count:-0}
        na_count=${na_count:-0}

        local total=$((pass_count + fail_count))
        local score=0
        if [[ $total -gt 0 ]]; then
            score=$((pass_count * 100 / total))
        fi

        host_pass[${host}]="${pass_count}"
        host_fail[${host}]="${fail_count}"
        host_na[${host}]="${na_count}"
        host_score[${host}]="${score}"

        # Extract rule-result entries to a flat file: ruleid|host|result
        awk '
        /<rule-result / {
            match($0, /idref="([^"]+)"/, m)
            idref = m[1]
        }
        /<result>/ && idref != "" {
            match($0, /<result>([^<]+)<\/result>/, m)
            result = m[1]
            if (result == "pass" || result == "fail") {
                print idref "\t" result
            }
            idref = ""
        }
        ' "${xml_file}" > "${TMP_DIR}/ruleresults_${host}.tsv"

        # Extract rule definitions: ruleid|severity|title
        awk '
        /<Rule / && /id="/ {
            match($0, /id="([^"]+)"/, m)
            rid = m[1]
            sev = "unknown"
            if (match($0, /severity="([^"]+)"/, s)) sev = s[1]
        }
        /<title>/ && rid != "" {
            match($0, /<title>([^<]+)<\/title>/, m)
            if (m[1] != "") {
                gsub(/\|/, "-", m[1])
                print rid "\t" sev "\t" m[1]
                rid = ""
            }
        }
        ' "${xml_file}" > "${TMP_DIR}/ruledefs_${host}.tsv"
    done

    # Build merged failed-rules list: only rules where at least one host failed
    {
        for host in ${ALL_HOSTS}; do
            [[ -f "${TMP_DIR}/ruleresults_${host}.tsv" ]] && \
                awk -F'\t' '$2 == "fail" { print $1 }' "${TMP_DIR}/ruleresults_${host}.tsv" || true
        done
    } | sort -u > "${TMP_DIR}/failed_rule_ids.txt"

    # Build a combined rule definitions lookup (first host wins)
    {
        for host in ${ALL_HOSTS}; do
            [[ -f "${TMP_DIR}/ruledefs_${host}.tsv" ]] && cat "${TMP_DIR}/ruledefs_${host}.tsv" || true
        done
    } | awk -F'\t' '!seen[$1]++ { print }' > "${TMP_DIR}/ruledefs_merged.tsv"
}

# --- Generate Markdown report ------------------------------------------------
generate_markdown() {
    local summary_file="${OUTPUT_DIR}/CUI_Compliance_Summary_${TODAY}.md"
    log "Generating Markdown report: $(basename "${summary_file}")"

    {
        echo "# CUI Compliance Summary — ${TODAY_PRETTY}"
        echo ""
        echo "Generated: $(date '+%Y-%m-%d %H:%M:%S') on dc1.[DOMAIN.ORG]"
        echo ""
        echo "## Score Summary"
        echo ""
        echo "| System | Pass | Fail | N/A | Score | Report |"
        echo "|--------|------|------|-----|-------|--------|"
        for host in ${ALL_HOSTS}; do
            local report_name="cui_report_${host}_${TODAY}.html"
            local sc="${host_score[${host}]}"
            [[ "${sc}" != "—" ]] && sc="${sc}%"
            if [[ -f "${OUTPUT_DIR}/${report_name}" ]]; then
                echo "| ${host} | ${host_pass[${host}]} | ${host_fail[${host}]} | ${host_na[${host}]} | ${sc} | [${report_name}](${report_name}) |"
            else
                echo "| ${host} | ${host_pass[${host}]} | ${host_fail[${host}]} | ${host_na[${host}]} | ${sc} | ${report_name} *(not collected)* |"
            fi
        done
        echo ""
        echo "## Failed Rules by System"
        echo ""

        if [[ ! -s "${TMP_DIR}/failed_rule_ids.txt" ]]; then
            echo "*No failed rules detected across any system.*"
        else
            echo "| Rule ID | Description | Severity | dc1 | ws-a | ws-b | ws-c |"
            echo "|---------|-------------|----------|-----|--------|-------------|------------|"
            while IFS= read -r ruleid; do
                local short_id="${ruleid##*rule_}"
                local desc="" sev="unknown"
                # Look up description
                local defline
                defline=$(awk -F'\t' -v r="${ruleid}" '$1 == r { print $2 "\t" $3; exit }' "${TMP_DIR}/ruledefs_merged.tsv")
                if [[ -n "${defline}" ]]; then
                    sev="${defline%%	*}"
                    desc="${defline#*	}"
                fi
                [[ -z "${desc}" ]] && desc="${short_id}"
                [[ ${#desc} -gt 60 ]] && desc="${desc:0:57}..."

                local row="| ${short_id} | ${desc} | ${sev} |"
                for host in ${ALL_HOSTS}; do
                    local result="—"
                    if [[ -f "${TMP_DIR}/ruleresults_${host}.tsv" ]]; then
                        result=$(awk -F'\t' -v r="${ruleid}" '$1 == r { print $2; exit }' "${TMP_DIR}/ruleresults_${host}.tsv")
                    fi
                    case "${result}" in
                        fail) row+=" **FAIL** |" ;;
                        pass) row+=" PASS |" ;;
                        *)    row+=" — |" ;;
                    esac
                done
                echo "${row}"
            done < "${TMP_DIR}/failed_rule_ids.txt"
        fi

        echo ""
        echo "---"
        echo "*Report generated by collect_openscap_results.sh*"
    } > "${summary_file}"

    log "Markdown report: ${summary_file}"
}

# --- Generate HTML dashboard -------------------------------------------------
generate_html_dashboard() {
    local dashboard_file="${WEB_DIR}/openscap-dashboard.html"
    mkdir -p "${WEB_REPORTS_DIR}"
    log "Generating HTML dashboard: ${dashboard_file}"

    # Copy collected HTML reports to web-accessible directory
    for host in ${ALL_HOSTS}; do
        local src="${OUTPUT_DIR}/cui_report_${host}_${TODAY}.html"
        if [[ -f "${src}" ]]; then
            cp "${src}" "${WEB_REPORTS_DIR}/"
        fi
    done

    # Compute overall score for header
    local total_pass=0 total_fail=0
    for host in ${ALL_HOSTS}; do
        local p="${host_pass[${host}]}"
        local f="${host_fail[${host}]}"
        [[ "${p}" == "—" ]] && continue
        total_pass=$((total_pass + p))
        total_fail=$((total_fail + f))
    done
    local overall_score="N/A"
    local overall_total=$((total_pass + total_fail))
    if [[ $overall_total -gt 0 ]]; then
        overall_score="$((total_pass * 100 / overall_total))%"
    fi

    # Count systems reporting
    local systems_reporting=0
    for host in ${ALL_HOSTS}; do
        [[ "${host_pass[${host}]}" != "—" ]] && systems_reporting=$((systems_reporting + 1))
    done

    local failed_count=0
    [[ -s "${TMP_DIR}/failed_rule_ids.txt" ]] && failed_count=$(wc -l < "${TMP_DIR}/failed_rule_ids.txt")

    cat > "${dashboard_file}" <<'HTMLHEADER'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>OpenSCAP CUI Compliance Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            margin-bottom: 25px;
            text-align: center;
        }
        .header h1 { color: #667eea; font-size: 32px; margin-bottom: 8px; }
        .header .subtitle { color: #666; font-size: 15px; }
        .header .domain { color: #999; font-size: 13px; margin-top: 4px; }
        .nav-link {
            display: inline-block;
            margin-top: 12px;
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }
        .nav-link:hover { text-decoration: underline; }

        .kpi-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .kpi-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .kpi-value { font-size: 36px; font-weight: 700; }
        .kpi-label { font-size: 13px; color: #666; margin-top: 4px; }
        .kpi-good { color: #28a745; }
        .kpi-warn { color: #ffc107; }
        .kpi-bad  { color: #dc3545; }
        .kpi-info { color: #667eea; }

        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 25px;
        }
        .card h2 {
            color: #667eea;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }

        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th {
            background: #667eea;
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        td { padding: 9px 12px; border-bottom: 1px solid #eee; }
        tr:hover td { background: #f8f9ff; }

        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-pass { background: #d4edda; color: #155724; }
        .badge-fail { background: #f8d7da; color: #721c24; }
        .badge-na   { background: #e2e3e5; color: #383d41; }

        .score-bar {
            display: inline-block;
            width: 80px;
            height: 10px;
            background: #eee;
            border-radius: 5px;
            overflow: hidden;
            vertical-align: middle;
            margin-right: 6px;
        }
        .score-fill {
            height: 100%;
            border-radius: 5px;
            transition: width 0.3s;
        }

        .severity-high   { color: #dc3545; font-weight: 600; }
        .severity-medium { color: #fd7e14; font-weight: 600; }
        .severity-low    { color: #28a745; }
        .severity-unknown { color: #6c757d; }

        a.report-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        a.report-link:hover { text-decoration: underline; }

        .empty-state {
            text-align: center;
            padding: 30px;
            color: #999;
            font-style: italic;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 20px;
            padding: 15px;
            font-size: 13px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }

        @media (max-width: 768px) {
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
            .header h1 { font-size: 24px; }
            table { font-size: 12px; }
        }
    </style>
</head>
<body>
<div class="container">
HTMLHEADER

    # Header section
    cat >> "${dashboard_file}" <<EOF
    <div class="header">
        <h1>OpenSCAP CUI Compliance Dashboard</h1>
        <div class="subtitle">NIST 800-171 CUI Profile &mdash; All CPN Systems</div>
        <div class="domain">dc1.[DOMAIN.ORG] &bull; Last updated: $(date '+%Y-%m-%d %H:%M:%S')</div>
        <a href="switchboard.html" class="nav-link">&larr; Back to Control Center</a>
    </div>
EOF

    # KPI row
    local score_class="kpi-good"
    if [[ "${overall_score}" != "N/A" ]]; then
        local score_num="${overall_score%\%}"
        [[ $score_num -lt 95 ]] && score_class="kpi-warn"
        [[ $score_num -lt 80 ]] && score_class="kpi-bad"
    else
        score_class="kpi-info"
    fi

    local fail_class="kpi-good"
    [[ $failed_count -gt 0 ]] && fail_class="kpi-warn"
    [[ $failed_count -gt 5 ]] && fail_class="kpi-bad"

    cat >> "${dashboard_file}" <<EOF
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-value ${score_class}">${overall_score}</div>
            <div class="kpi-label">Overall Compliance Score</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value kpi-info">${systems_reporting} / 4</div>
            <div class="kpi-label">Systems Reporting</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value kpi-good">${total_pass}</div>
            <div class="kpi-label">Total Rules Passed</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value ${fail_class}">${failed_count}</div>
            <div class="kpi-label">Unique Failed Rules</div>
        </div>
    </div>
EOF

    # Score summary table
    cat >> "${dashboard_file}" <<'EOF'
    <div class="card">
        <h2>System Score Summary</h2>
        <table>
            <thead>
                <tr><th>System</th><th>Pass</th><th>Fail</th><th>N/A</th><th>Score</th><th>Full Report</th></tr>
            </thead>
            <tbody>
EOF

    for host in ${ALL_HOSTS}; do
        local p="${host_pass[${host}]}" f="${host_fail[${host}]}" n="${host_na[${host}]}" s="${host_score[${host}]}"
        local report_name="cui_report_${host}_${TODAY}.html"
        local report_link=""
        if [[ -f "${WEB_REPORTS_DIR}/${report_name}" ]]; then
            report_link="<a href=\"openscap/${report_name}\" class=\"report-link\" target=\"_blank\">${report_name}</a>"
        else
            report_link="<span style=\"color:#999\">not collected</span>"
        fi

        local score_color="#28a745" fill_width="0"
        if [[ "${s}" != "—" ]]; then
            fill_width="${s}"
            [[ $s -lt 95 ]] && score_color="#ffc107"
            [[ $s -lt 80 ]] && score_color="#dc3545"
        fi

        cat >> "${dashboard_file}" <<EOF
                <tr>
                    <td><strong>${host}</strong></td>
                    <td>${p}</td>
                    <td>${f}</td>
                    <td>${n}</td>
                    <td>
EOF
        if [[ "${s}" != "—" ]]; then
            cat >> "${dashboard_file}" <<EOF
                        <span class="score-bar"><span class="score-fill" style="width:${fill_width}%;background:${score_color}"></span></span>${s}%
EOF
        else
            echo "                        <span class=\"badge badge-na\">N/A</span>" >> "${dashboard_file}"
        fi
        cat >> "${dashboard_file}" <<EOF
                    </td>
                    <td>${report_link}</td>
                </tr>
EOF
    done

    echo "            </tbody>" >> "${dashboard_file}"
    echo "        </table>" >> "${dashboard_file}"
    echo "    </div>" >> "${dashboard_file}"

    # Failed rules table
    cat >> "${dashboard_file}" <<'EOF'
    <div class="card">
        <h2>Failed Rules by System</h2>
EOF

    if [[ ! -s "${TMP_DIR}/failed_rule_ids.txt" ]]; then
        echo '        <div class="empty-state">No failed rules detected across any system. Full compliance achieved.</div>' >> "${dashboard_file}"
    else
        cat >> "${dashboard_file}" <<'EOF'
        <div style="overflow-x:auto">
        <table>
            <thead>
                <tr><th>Rule ID</th><th>Description</th><th>Severity</th><th>dc1</th><th>ws-a</th><th>ws-b</th><th>ws-c</th></tr>
            </thead>
            <tbody>
EOF
        while IFS= read -r ruleid; do
            local short_id="${ruleid##*rule_}"
            local desc="" sev="unknown"
            local defline
            defline=$(awk -F'\t' -v r="${ruleid}" '$1 == r { print $2 "\t" $3; exit }' "${TMP_DIR}/ruledefs_merged.tsv")
            if [[ -n "${defline}" ]]; then
                sev="${defline%%	*}"
                desc="${defline#*	}"
            fi
            [[ -z "${desc}" ]] && desc="${short_id}"
            # HTML-escape angle brackets in descriptions
            desc="${desc//</&lt;}"
            desc="${desc//>/&gt;}"
            [[ ${#desc} -gt 80 ]] && desc="${desc:0:77}..."

            local sev_class="severity-unknown"
            case "${sev}" in
                high)   sev_class="severity-high" ;;
                medium) sev_class="severity-medium" ;;
                low)    sev_class="severity-low" ;;
            esac

            echo "                <tr>" >> "${dashboard_file}"
            echo "                    <td><code>${short_id}</code></td>" >> "${dashboard_file}"
            echo "                    <td>${desc}</td>" >> "${dashboard_file}"
            echo "                    <td><span class=\"${sev_class}\">${sev}</span></td>" >> "${dashboard_file}"

            for host in ${ALL_HOSTS}; do
                local result="—"
                if [[ -f "${TMP_DIR}/ruleresults_${host}.tsv" ]]; then
                    result=$(awk -F'\t' -v r="${ruleid}" '$1 == r { print $2; exit }' "${TMP_DIR}/ruleresults_${host}.tsv")
                fi
                case "${result}" in
                    fail) echo "                    <td><span class=\"badge badge-fail\">FAIL</span></td>" >> "${dashboard_file}" ;;
                    pass) echo "                    <td><span class=\"badge badge-pass\">PASS</span></td>" >> "${dashboard_file}" ;;
                    *)    echo "                    <td><span class=\"badge badge-na\">&mdash;</span></td>" >> "${dashboard_file}" ;;
                esac
            done
            echo "                </tr>" >> "${dashboard_file}"
        done < "${TMP_DIR}/failed_rule_ids.txt"

        echo "            </tbody>" >> "${dashboard_file}"
        echo "        </table>" >> "${dashboard_file}"
        echo "        </div>" >> "${dashboard_file}"
    fi

    echo "    </div>" >> "${dashboard_file}"

    # Footer
    cat >> "${dashboard_file}" <<'EOF'
    <div class="footer">
        <strong>CyberHygiene Project</strong> | [ORGANIZATION]<br>
        NIST 800-171 CUI Profile (SCAP Security Guide) | FIPS 140-2 Enabled<br>
        <small>Classification: CONTROLLED UNCLASSIFIED INFORMATION (CUI)</small>
    </div>
</div>
</body>
</html>
EOF

    chown apache:apache "${dashboard_file}" 2>/dev/null || true
    chown -R apache:apache "${WEB_REPORTS_DIR}" 2>/dev/null || true
    log "HTML dashboard: ${dashboard_file}"
}

# --- Generate all reports ----------------------------------------------------
generate_report() {
    parse_results
    generate_markdown
    generate_html_dashboard
    echo ""
}

# --- Main --------------------------------------------------------------------
MODE="--collect-only"
if [[ "${1:-}" == "--scan-and-collect" ]]; then
    MODE="--scan-and-collect"
elif [[ "${1:-}" != "" && "${1:-}" != "--collect-only" ]]; then
    echo "Usage: $0 [--collect-only | --scan-and-collect]"
    exit 1
fi

echo "========================================"
echo "OpenSCAP CUI Results Collection"
echo "Mode: ${MODE}"
echo "Date: ${TODAY_PRETTY}"
echo "========================================"
echo ""

if [[ "${MODE}" == "--scan-and-collect" ]]; then
    trigger_scans
fi

collect_results
generate_report

echo "========================================"
echo "Collection complete!"
echo "Reports:   ${OUTPUT_DIR}/"
echo "Summary:   CUI_Compliance_Summary_${TODAY}.md"
echo "Dashboard: https://dc1.[DOMAIN.ORG]/dashboard/openscap-dashboard.html"
echo "========================================"
