# Shubham Rajput
# 24BCE0869
# NetDoctor - Layer-by-Layer Network Troubleshooting and Performance Analysis

import html
from datetime import datetime

import pandas as pd
import streamlit as st

from checks import LAYER_NAMES, OK, WARN, FAIL, run_all, summarize

def make_favicon():
    """UI-ONLY: draw the NetDoctor mark (blue tile with a pulse line) as the tab icon."""
    try:
        from PIL import Image, ImageDraw

        size, scale = 64, 4
        big = size * scale
        img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 0.24, fill=(47, 111, 237, 255))
        unit = big / 24
        points = [(2, 12), (7, 12), (9.5, 5), (13, 19), (15.5, 12), (22, 12)]
        points = [(x * unit, y * unit) for x, y in points]
        width = int(unit * 2.3)
        draw.line(points, fill=(255, 255, 255, 255), width=width, joint="curve")
        for x, y in (points[0], points[-1]):
            draw.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=(255, 255, 255, 255))
        return img.resize((size, size), Image.LANCZOS)
    except Exception:
        return "🌐"


st.set_page_config(
    page_title="NetDoctor | Network Diagnostics",
    page_icon=make_favicon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- THEME (UI-ONLY) -----------------------------
# Pure CSS: no Streamlit theme override, so the built-in light/dark switch keeps
# working. Surfaces use translucent greys, so they adapt to either theme.
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

      :root {
        --nd-line: rgba(128,128,128,.26);
        --nd-soft: rgba(128,128,128,.13);
        --nd-wash: rgba(128,128,128,.07);
        --nd-ok: #1f9d6b;
        --nd-warn: #cf8a00;
        --nd-fail: #e5484d;
        --nd-accent: #2f6fed;
        --nd-r: 12px;
        --nd-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        --nd-sans: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
      }

      .stApp {font-family: var(--nd-sans);}
      .block-container, [data-testid="stMainBlockContainer"] {padding-top: 4.6rem; padding-bottom: 3rem; max-width: 1240px;}

      /* status tokens (class on any element sets --c and --t for its children) */
      .s-ok   {--c: var(--nd-ok);   --t: rgba(31,157,107,.10);}
      .s-warn {--c: var(--nd-warn); --t: rgba(207,138,0,.11);}
      .s-fail {--c: var(--nd-fail); --t: rgba(229,72,77,.11);}

      /* masthead */
      .mast-t {display: flex; align-items: center; gap: .7rem; font-size: 1.9rem; font-weight: 700; letter-spacing: -.035em; line-height: 1.15;}
      .logo {flex: 0 0 36px; width: 36px; height: 36px; border-radius: 10px; background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpolyline points='2,12 7,12 9.5,5 13,19 15.5,12 22,12' fill='none' stroke='white' stroke-width='2.3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center / 72% no-repeat, var(--nd-accent);}
      .mast-s {font-size: 1rem; opacity: .72; margin: .35rem 0 0 0;}
      .small-muted {font-size: .86rem; opacity: .62; line-height: 1.5; margin-top: .35rem;}
      .rule {height: 1px; background: var(--nd-line); margin: 1rem 0 .4rem 0;}

      /* section headers */
      .sec {margin: 2rem 0 .85rem 0;}
      .sec-t {font-size: 1.12rem; font-weight: 700; letter-spacing: -.015em;}
      .sec-h {font-size: .86rem; opacity: .6; margin-top: 2px;}
      .sub {font-size: .74rem; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; opacity: .55; margin: 1rem 0 .5rem 0;}

      /* landing state */
      .empty {border: 1px dashed var(--nd-line); border-radius: var(--nd-r); padding: 1.6rem 1.5rem; margin: .8rem 0 0 0; background: var(--nd-wash);}
      .e-t {font-size: 1.15rem; font-weight: 700; letter-spacing: -.01em;}
      .e-b {opacity: .72; margin-top: .25rem;}
      .feat {border: 1px solid var(--nd-line); border-radius: var(--nd-r); padding: 18px 18px 20px 18px; background: var(--nd-wash); min-height: 168px; transition: border-color .15s ease, transform .15s ease;}
      .feat:hover {border-color: var(--nd-accent); transform: translateY(-2px);}
      .feat-badge {display: inline-block; font-family: var(--nd-mono); font-size: .74rem; font-weight: 500; padding: 3px 9px; border-radius: 999px; background: var(--nd-accent); color: #fff;}
      .feat-h {font-weight: 700; margin: .75rem 0 .4rem 0; font-size: 1.02rem;}
      .feat-b {font-size: .9rem; opacity: .74; line-height: 1.55;}

      /* overall status banner */
      .banner {display: flex; flex-wrap: wrap; align-items: flex-start; gap: 18px; padding: 22px 24px; border: 1px solid var(--nd-line); border-radius: var(--nd-r); background: var(--t); box-shadow: inset 5px 0 0 var(--c); margin-top: .6rem;}
      .b-ic {flex: 0 0 48px; height: 48px; border-radius: 50%; background: var(--c); color: #fff; font-size: 1.45rem; font-weight: 700; display: grid; place-items: center; line-height: 1;}
      .b-main {flex: 1 1 380px; min-width: 0;}
      .b-k {font-size: .72rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--c);}
      .b-t {font-size: 1.5rem; font-weight: 700; letter-spacing: -.025em; margin-top: 2px;}
      .b-d {line-height: 1.65; opacity: .86; margin-top: 6px; max-width: 80ch;}
      .b-side {margin-left: auto; text-align: right;}
      .b-m {font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; opacity: .55;}
      .b-mv {font-family: var(--nd-mono); font-size: .86rem; margin-top: 2px;}
      .tally {display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;}
      .b-side .tally {justify-content: flex-end;}
      .tally span {display: inline-flex; align-items: center; font-size: .78rem; font-weight: 600; color: var(--c); padding: 3px 11px 3px 9px; border-radius: 999px; background: var(--t); border: 1px solid var(--c);}
      .tally i {width: 7px; height: 7px; border-radius: 50%; background: var(--c); margin-right: 7px;}

      /* device info */
      .kv {display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 14px;}
      .kv-i {border: 1px solid var(--nd-line); border-radius: var(--nd-r); background: var(--nd-wash); padding: 12px 16px; min-width: 0;}
      .kv-k {font-size: .72rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; opacity: .55;}
      .kv-v {font-family: var(--nd-mono); font-size: 1.05rem; font-weight: 500; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}

      /* OSI stack */
      .stack {display: flex; flex-direction: column; gap: 8px;}
      .row {display: grid; grid-template-columns: 54px 150px 1fr 118px; align-items: center; gap: 14px; padding: 12px 16px 12px 18px; border: 1px solid var(--nd-line); border-radius: 10px; background: var(--t); box-shadow: inset 4px 0 0 var(--c); transition: transform .15s ease;}
      .row:hover {transform: translateX(2px);}
      .r-no {font-family: var(--nd-mono); font-size: .86rem; font-weight: 500; opacity: .6;}
      .r-nm {font-weight: 700;}
      .r-chk {display: flex; flex-wrap: wrap; gap: 6px;}
      .chip {display: inline-flex; align-items: center; font-size: .78rem; padding: 3px 10px 3px 8px; border-radius: 999px; border: 1px solid var(--nd-line); background: rgba(128,128,128,.08);}
      .chip i {width: 7px; height: 7px; border-radius: 50%; background: var(--c); margin-right: 7px; flex: 0 0 auto;}
      .chip em {font-style: normal; font-family: var(--nd-mono); font-size: .74rem; opacity: .65; margin-left: 7px;}
      .chip-none {font-size: .8rem; opacity: .55;}
      .r-st {justify-self: end; font-size: .78rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--c);}
      .r-st i {display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--c); margin-right: 7px;}
      @media (max-width: 900px) {
        .row {grid-template-columns: 44px 1fr; row-gap: 8px;}
        .r-chk {grid-column: 1 / -1;}
        .r-st {justify-self: start; grid-column: 1 / -1;}
        .b-side {margin-left: 0; text-align: left;}
        .b-side .tally {justify-content: flex-start;}
      }

      /* recommendations */
      .rec {background: var(--t); border: 1px solid var(--nd-soft); border-left: 4px solid var(--c); padding: 13px 18px; border-radius: 4px 10px 10px 4px; margin: 0 0 10px 0;}
      .rec-h {font-weight: 700;}
      .rec-b {font-size: .92rem; line-height: 1.62; opacity: .82; margin-top: 3px;}

      /* metric tiles */
      [data-testid="stMetric"] {background: var(--nd-wash); border: 1px solid var(--nd-line); border-radius: 10px; padding: 12px 15px; transition: border-color .15s ease;}
      [data-testid="stMetric"]:hover {border-color: var(--nd-accent);}
      [data-testid="stMetricLabel"] p {font-size: .72rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; opacity: .62;}
      [data-testid="stMetricValue"] {font-family: var(--nd-mono); font-size: 1.3rem; font-weight: 500; font-variant-numeric: tabular-nums;}

      /* tabs */
      .stTabs [data-baseweb="tab-list"] {gap: 1.6rem; border-bottom: 1px solid var(--nd-line);}
      .stTabs [data-baseweb="tab"] {height: auto; padding: .55rem 0; font-weight: 600;}
      .stTabs [data-baseweb="tab-highlight"] {height: 3px; border-radius: 3px; background: var(--nd-accent);}

      /* test guide */
      .guide {display: grid; grid-template-columns: 56px 1fr; gap: 4px; padding: 14px 0; border-bottom: 1px solid var(--nd-soft);}
      .g-no {font-family: var(--nd-mono); font-size: .82rem; opacity: .55; padding-top: 2px;}
      .g-h {font-weight: 700;}
      .g-b {font-size: .93rem; line-height: 1.62; opacity: .78; margin-top: 2px;}

      /* sidebar */
      .brand {display: flex; align-items: center; gap: .6rem; font-size: 1.3rem; font-weight: 700; letter-spacing: -.025em;}
      .brand .logo {flex-basis: 28px; width: 28px; height: 28px; border-radius: 8px;}
      .brand-s {font-size: .84rem; opacity: .62; margin-top: 4px;}
      .cov {display: grid; grid-template-columns: 34px 1fr; font-size: .88rem; padding: 5px 0; border-bottom: 1px solid var(--nd-soft); transition: padding-left .15s ease;}
      .cov:hover {padding-left: 4px;}
      .cov b {font-family: var(--nd-mono); font-weight: 500; opacity: .55;}

      /* controls */
      div.stButton > button, div.stDownloadButton > button {border-radius: 10px; font-weight: 600; min-height: 2.7rem; letter-spacing: .01em;}
      div.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {background: var(--nd-accent); border: 1px solid var(--nd-accent); color: #fff;}
      div.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {filter: brightness(1.12); border-color: var(--nd-accent); color: #fff;}
      div.stButton > button:active, div.stDownloadButton > button:active {transform: translateY(1px);}
      [data-testid="stDataFrame"] {border: 1px solid var(--nd-soft); border-radius: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_ICON = {OK: "🟢", WARN: "🟠", FAIL: "🔴"}
STATUS_LABEL = {OK: "Healthy", WARN: "Warning", FAIL: "Failed"}
STATUS_COLOR = {OK: "#20a464", WARN: "#d98b17", FAIL: "#d94b4b"}
STATUS_CLASS = {OK: "s-ok", WARN: "s-warn", FAIL: "s-fail"}


def fmt(value, suffix="", digits=2):
    if value is None or value == "":
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}{suffix}"
    return f"{value}{suffix}"


def layer_status(results, layer):
    checks = [item for item in results if item["layer"] == layer]
    if not checks:
        return WARN
    if any(item["status"] == FAIL for item in checks):
        return FAIL
    if any(item["status"] == WARN for item in checks):
        return WARN
    return OK


# ----------------------------- PRESENTATION HELPERS (UI-ONLY) -----------------------------
def section(title, hint=None):
    hint_html = f'<div class="sec-h">{html.escape(hint)}</div>' if hint else ""
    st.markdown(
        f'<div class="sec"><div class="sec-t">{html.escape(title)}</div>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def sublabel(text):
    st.markdown(f'<div class="sub">{html.escape(text)}</div>', unsafe_allow_html=True)


def tally_html(health):
    states = [health.get(number) or WARN for number in LAYER_NAMES]
    parts = [
        f'<span class="{STATUS_CLASS[state]}"><i></i>{states.count(state)} {STATUS_LABEL[state]}</span>'
        for state in (OK, WARN, FAIL)
    ]
    return f'<div class="tally">{"".join(parts)}</div>'


def status_banner(verdict, level, timestamp, health):
    cls = {"error": "s-fail", "warning": "s-warn", "success": "s-ok"}[level]
    glyph = {"error": "✕", "warning": "!", "success": "✓"}[level]
    title = {"error": "Problem detected", "warning": "Needs attention", "success": "Network healthy"}[level]
    st.markdown(
        f'<div class="banner {cls}"><div class="b-ic">{glyph}</div>'
        f'<div class="b-main"><div class="b-k">Overall status</div>'
        f'<div class="b-t">{title}</div>'
        f'<div class="b-d">{html.escape(str(verdict))}</div></div>'
        f'<div class="b-side"><div class="b-m">Last completed run</div>'
        f'<div class="b-mv">{html.escape(str(timestamp))}</div>{tally_html(health)}</div></div>',
        unsafe_allow_html=True,
    )


def device_card(info):
    items = [
        ("Hostname", str(info.get("Hostname", "N/A"))),
        ("Local IP Address", str(info.get("Local IP", "N/A"))),
        ("Default Gateway", str(info.get("Default Gateway") or "Not detected")),
    ]
    cells = "".join(
        f'<div class="kv-i"><div class="kv-k">{html.escape(k)}</div>'
        f'<div class="kv-v" title="{html.escape(v)}">{html.escape(v)}</div></div>'
        for k, v in items
    )
    st.markdown(f'<div class="kv">{cells}</div>', unsafe_allow_html=True)


def layer_stack(health, results):
    rows = []
    # OSI convention: Layer 7 at the top of the stack, Layer 1 at the bottom.
    for number, name in sorted(LAYER_NAMES.items(), reverse=True):
        status = health.get(number) or WARN
        chips = []
        for item in results:
            if item["layer"] != number:
                continue
            value = item.get("value")
            extra = f"<em>{value:.1f} ms</em>" if isinstance(value, (int, float)) else ""
            chips.append(
                f'<span class="chip {STATUS_CLASS.get(item["status"], "s-warn")}">'
                f'<i></i>{html.escape(str(item["name"]))}{extra}</span>'
            )
        if not chips:
            chips = ['<span class="chip-none">No checks returned</span>']
        rows.append(
            f'<div class="row {STATUS_CLASS.get(status, "s-warn")}">'
            f'<div class="r-no">L{number}</div>'
            f'<div class="r-nm">{html.escape(name)}</div>'
            f'<div class="r-chk">{"".join(chips)}</div>'
            f'<div class="r-st"><i></i>{html.escape(STATUS_LABEL.get(status, str(status)))}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="stack">{"".join(rows)}</div>', unsafe_allow_html=True)


def recommendation_block(icon, heading, detail):
    cls = {"🔴": "s-fail", "🟠": "s-warn"}.get(icon, "s-ok")
    st.markdown(
        f'<div class="rec {cls}"><div class="rec-h">{html.escape(str(heading))}</div>'
        f'<div class="rec-b">{html.escape(str(detail))}</div></div>',
        unsafe_allow_html=True,
    )


def recommendations(results, internet_ping):
    """Generate prioritized advice from diagnostic evidence."""
    notes = []
    by_name = {item["name"]: item for item in results}

    def status(name):
        item = by_name.get(name)
        return item.get("status") if item else None

    def detail(name):
        item = by_name.get(name)
        return item.get("detail", "") if item else ""

    interface = status("Network Interface")
    local_ip = status("Local IP")
    arp = status("Gateway ARP")
    gateway = status("Gateway Ping")
    internet = status("Internet Ping")
    tcp = status("TCP Connection")
    tls = status("TLS Session Setup")
    dns = status("DNS Lookup")
    cert = status("Certificate Validity")
    https = status("HTTPS Request")

    # 1. Highest priority: local connectivity.
    if interface == FAIL:
        notes.append((
            "🔴",
            "Check the network adapter",
            "Enable the Wi-Fi or Ethernet adapter. Confirm that "
            "the device is connected to a network, then rerun diagnosis."
        ))

    if local_ip == FAIL:
        notes.append((
            "🔴",
            "Check local IP configuration",
            "Verify adapter settings and DHCP configuration. "
            "Reconnect to the network and check whether an IP address "
            "is assigned."
        ))

    # 2. Gateway discovery and reachability need context.
    external_works = tcp == OK or https == OK

    if arp in (WARN, FAIL):
        notes.append((
            "🟠",
            "Check gateway discovery",
            f"{detail('Gateway ARP')} Reconnect to the network and "
            "rerun the test. A missing ARP entry alone does not prove "
            "a gateway failure."
        ))

    if gateway in (WARN, FAIL):
        if external_works:
            notes.append((
                "🟠",
                "Interpret gateway ping carefully",
                "TCP or HTTPS connectivity succeeded. The gateway "
                "may restrict ICMP replies, so do not conclude that "
                "the local network is down from ping alone."
            ))
        else:
            notes.append((
                "🟠",
                "Check gateway and routing",
                "Verify the default gateway and active route. "
                "Reconnect to Wi-Fi or Ethernet and repeat the tests."
            ))

    # 3. Performance measurements.
    latency = internet_ping.get("latency_ms")
    loss = internet_ping.get("packet_loss")
    jitter = internet_ping.get("jitter_ms")

    if latency is not None and latency > 150:
        notes.append((
            "🟠",
            "Investigate high latency",
            f"Average internet ping was {latency:.1f} ms. Repeat "
            "the test and compare another destination. Wi-Fi quality, "
            "routing and network congestion may affect latency."
        ))

    if loss is not None and loss > 0:
        notes.append((
            "🟠",
            "Investigate packet loss",
            f"The ping test reported {loss:.1f}% packet loss. "
            "Repeat the measurement because ICMP loss may not reflect "
            "all application traffic."
        ))

    if jitter is not None and jitter > 30:
        notes.append((
            "🟠",
            "Check latency variation",
            f"Measured jitter was {jitter:.1f} ms. Repeat the test "
            "and compare results. High variation may affect calls, "
            "gaming and other real-time applications."
        ))

    # 4. DNS advice should not claim all name resolution is broken
    # merely because one lookup failed.
    if dns in (WARN, FAIL):
        notes.append((
            "🟠",
            "Investigate DNS resolution",
            f"{detail('DNS Lookup')} Retry the lookup and test "
            "another hostname. Check the configured resolver before "
            "changing DNS settings."
        ))

    # 5. TCP connectivity.
    if tcp in (WARN, FAIL):
        if https == OK:
            notes.append((
                "🟠",
                "Review the TCP test result",
                "The TCP test reported a problem, but HTTPS succeeded. "
                "The tests may use different destinations or conditions; "
                "repeat both before diagnosing a transport failure."
            ))
        else:
            notes.append((
                "🔴",
                "Investigate TCP connectivity",
                f"{detail('TCP Connection')} Check routing, firewall "
                "rules, proxy settings and whether the destination "
                "service is reachable."
            ))

    # 6. TLS and certificate findings.
    if cert in (WARN, FAIL):
        notes.append((
            "🔴" if cert == FAIL else "🟠",
            "Review certificate validity",
            f"{detail('Certificate Validity')} Verify the system "
            "date and certificate information before proceeding."
        ))

    if tls in (WARN, FAIL):
        notes.append((
            "🟠",
            "Investigate secure-session setup",
            f"{detail('TLS Session Setup')} Check system date/time, "
            "certificate trust, proxy behavior and destination "
            "availability. A failed handshake alone does not identify "
            "the root cause."
        ))

    # 7. Application-level HTTPS result.
    if https in (WARN, FAIL):
        notes.append((
            "🟠",
            "Investigate the HTTPS request",
            f"{detail('HTTPS Request')} Review the HTTP status or "
            "error, TLS configuration, proxy settings and destination "
            "availability."
        ))

    # 8. Only show the success message when no actionable warning exists.
    if not notes:
        notes.append((
            "✅",
            "No immediate issue detected",
            "All reported checks passed for the tested interface and "
            "destinations. This is a point-in-time assessment, not "
            "a guarantee that every network service is healthy."
        ))

    return notes



# ----------------------------- SESSION STATE -----------------------------
if "diagnostic_history" not in st.session_state:
    st.session_state.diagnostic_history = []
if "latest_diagnostics" not in st.session_state:
    st.session_state.latest_diagnostics = None

# ----------------------------- SIDEBAR -----------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><span class="logo"></span>NetDoctor</div>'
        '<div class="brand-s">Layer-aware network troubleshooting</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    sublabel("Diagnostic coverage")
    st.markdown(
        "".join(
            f'<div class="cov"><b>L{number}</b><span>{html.escape(name)}</span></div>'
            for number, name in LAYER_NAMES.items()
        ),
        unsafe_allow_html=True,
    )
    st.divider()
    sublabel("Project stack")
    st.caption("Python · Streamlit · psutil · dnspython")
    if st.button("Clear performance history", use_container_width=True):
        st.session_state.diagnostic_history = []
        st.rerun()
    st.caption("Checks are practical indicators mapped to OSI layers; they do not fully test every function of each layer.")

# ----------------------------- HEADER -----------------------------
try:
    head_col, run_col = st.columns([3.4, 1], vertical_alignment="center")
except TypeError:  # older Streamlit without vertical_alignment
    head_col, run_col = st.columns([3.4, 1])
with head_col:
    st.markdown(
        """
        <div class="mast-t"><span class="logo"></span>NetDoctor</div>
        <div class="mast-s">Layer-Aware Network Troubleshooting &amp; Performance Analysis</div>
        <div class="small-muted">Checks interface status, gateway discovery, IP connectivity, TCP, TLS, DNS and HTTPS. A run may take several seconds.</div>
        """,
        unsafe_allow_html=True,
    )
with run_col:
    run_clicked = st.button("Run Full Diagnosis", type="primary", use_container_width=True)
st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

if run_clicked:
    with st.spinner("Running layer-by-layer diagnostics…"):
        try:
            info, results, internet_ping = run_all()
            health, verdict = summarize(results)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            snapshot = {
                "info": info,
                "results": results,
                "internet_ping": internet_ping,
                "health": health,
                "verdict": verdict,
                "timestamp": timestamp,
            }
            st.session_state.latest_diagnostics = snapshot

            by_name = {item["name"]: item for item in results}
            st.session_state.diagnostic_history.append({
                "Run": len(st.session_state.diagnostic_history) + 1,
                "Time": timestamp,
                "Internet ping (ms)": internet_ping.get("latency_ms"),
                "Packet loss (%)": internet_ping.get("packet_loss"),
                "Jitter (ms)": internet_ping.get("jitter_ms"),
                "DNS lookup (ms)": by_name.get("DNS Lookup", {}).get("value"),
                "TCP connect (ms)": by_name.get("TCP Connection", {}).get("value"),
                "TLS setup (ms)": by_name.get("TLS Session Setup", {}).get("value"),
                "HTTPS request (ms)": by_name.get("HTTPS Request", {}).get("value"),
            })
        except Exception as error:
            st.error(f"The diagnostic run could not complete: {error}")
            st.info("Confirm checks.py is in the same folder as app.py and that the required dependencies are installed.")

snapshot = st.session_state.latest_diagnostics
if snapshot is None:
    st.markdown(
        '<div class="empty"><div class="e-t">No report yet</div>'
        '<div class="e-b">Run a diagnosis to populate your live network report.</div></div>',
        unsafe_allow_html=True,
    )
    section("What NetDoctor checks", "Seven OSI layers, grouped into four areas.")
    intro = st.columns(4)
    items = [
        ("L1–L2 · Local link", "Interface status, reported link speed and gateway ARP discovery."),
        ("L3 · Network", "Local IP, gateway reachability, internet ping, packet loss and jitter."),
        ("L4–L6 · Secure transport", "TCP connection, TLS setup, negotiated cipher and certificate validity."),
        ("L7 · Application", "DNS resolution and an HTTPS request to a test destination."),
    ]
    for col, (heading, description) in zip(intro, items):
        badge, _, title = heading.partition(" · ")
        with col:
            st.markdown(
                f'<div class="feat"><span class="feat-badge">{html.escape(badge)}</span>'
                f'<div class="feat-h">{html.escape(title)}</div>'
                f'<div class="feat-b">{html.escape(description)}</div></div>',
                unsafe_allow_html=True,
            )
else:
    info = snapshot["info"]
    results = snapshot["results"]
    internet_ping = snapshot["internet_ping"]
    health = snapshot["health"]
    verdict = snapshot["verdict"]

    # Overall status first: the answer, then the evidence.
    if FAIL in health.values():
        level = "error"
    elif WARN in health.values():
        level = "warning"
    else:
        level = "success"
    status_banner(verdict, level, snapshot["timestamp"], health)
    device_card(info)

    # Layer-by-layer stack
    section("OSI Layer Health", "Layer 7 sits at the top of the stack. Each row lists the checks run at that layer.")
    layer_stack(health, results)

    # Recommendations beside the numbers they refer to
    by_name = {item["name"]: item for item in results}
    perf_col, rec_col = st.columns([1, 1.2], gap="large")  # metrics left, recommendations right

    with rec_col:
        section("Diagnosis & Recommendations", "Prioritised from the evidence collected in this run.")
        advice = recommendations(results, internet_ping)
        for icon, heading, detail in advice:
            recommendation_block(icon, heading, detail)

    with perf_col:
        section("Performance Metrics", "Single-run measurements.")
        sublabel("Latency and reliability")
        a1, a2 = st.columns(2)
        a1.metric("Internet Ping", fmt(internet_ping.get("latency_ms"), " ms"))
        a2.metric("Packet Loss", fmt(internet_ping.get("packet_loss"), "%", 1))
        b1, b2 = st.columns(2)
        b1.metric("Jitter", fmt(internet_ping.get("jitter_ms"), " ms"))
        b2.metric("DNS Lookup", fmt(by_name.get("DNS Lookup", {}).get("value"), " ms"))
        sublabel("Connection timings")
        c1, c2 = st.columns(2)
        c1.metric("TCP Connect", fmt(by_name.get("TCP Connection", {}).get("value"), " ms"))
        c2.metric("TLS Session Setup", fmt(by_name.get("TLS Session Setup", {}).get("value"), " ms"))
        d1, _d2 = st.columns(2)
        d1.metric("HTTPS Response", fmt(by_name.get("HTTPS Request", {}).get("value"), " ms"))

    # Tabs keep the report organized and less overwhelming.
    section("Full Report", "Every check, run-to-run history and what each layer test means.")
    tab_results, tab_history, tab_notes = st.tabs(["Detailed Results", "Performance History", "Test Guide"])
    with tab_results:
        rows = []
        for item in results:
            rows.append({
                "Layer": f"L{item['layer']} — {LAYER_NAMES.get(item['layer'], 'Unknown')}",
                "Test": item["name"],
                "Status": STATUS_LABEL.get(item['status'], item['status']),
                "Value": item.get("value") if item.get("value") is not None else "—",
                "Details": item["detail"],
            })
        table_df = pd.DataFrame(rows)
        status_colors = {
            STATUS_LABEL[OK]: "#1f9d6b",
            STATUS_LABEL[WARN]: "#d9961a",
            STATUS_LABEL[FAIL]: "#e5484d",
        }
        styler = table_df.style
        paint = getattr(styler, "map", None) or styler.applymap
        styled = paint(
            lambda v: f"color: {status_colors.get(v, 'inherit')}; font-weight: 600;",
            subset=["Status"],
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
        csv_data = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
        st.download_button("Download diagnostic report (CSV)", csv_data, "netdoctor_diagnostic_report.csv", "text/csv")

    with tab_history:
        history = st.session_state.diagnostic_history
        if len(history) >= 2:
            history_df = pd.DataFrame(history)
            sublabel("Response-time comparison across runs")
            chart_columns = [
                "Internet ping (ms)", "DNS lookup (ms)", "TCP connect (ms)",
                "TLS setup (ms)", "HTTPS request (ms)",
            ]
            chart_df = history_df.set_index("Run")[chart_columns].dropna(axis=1, how="all")
            st.line_chart(chart_df, use_container_width=True)
            sublabel("Run-by-run measurements")
            st.dataframe(history_df, use_container_width=True, hide_index=True)
            st.download_button("Download performance history (CSV)", history_df.to_csv(index=False).encode("utf-8"), "netdoctor_performance_history.csv", "text/csv")
        elif history:
            st.info("Run Full Diagnosis again to compare measurements across multiple runs.")
            st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
        else:
            st.info("Performance history will appear here after a diagnosis.")

    with tab_notes:
        descriptions = {
            1: "Checks whether a network interface is active and reports the operating system's link-speed value. It cannot physically test the cable or radio signal quality.",
            2: "Looks for the gateway's MAC address in the local ARP table. A missing entry can be temporary or interface-specific.",
            3: "Checks local IP configuration and sends ICMP echo requests to the gateway and a public IP address. Some networks filter ping.",
            4: "Measures how long a TCP connection to the test host and port takes to establish.",
            5: "Measures TLS handshake time as a practical indicator of secure-session setup.",
            6: "Reports the negotiated TLS version/cipher and the peer certificate's remaining validity.",
            7: "Measures system DNS resolution and checks whether an HTTPS GET request succeeds against the test website.",
        }
        for number, name in LAYER_NAMES.items():
            st.markdown(
                f'<div class="guide"><div class="g-no">L{number}</div><div>'
                f'<div class="g-h">{html.escape(name)}</div>'
                f'<div class="g-b">{html.escape(descriptions[number])}</div></div></div>',
                unsafe_allow_html=True,
            )

st.divider()
st.caption("NetDoctor is a point-in-time diagnostic aid. Results can be affected by VPNs, firewalls, ICMP filtering, DNS caching, target availability and current network conditions.")
