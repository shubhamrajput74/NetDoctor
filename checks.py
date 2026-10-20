
# NetDoctor - Layer-by-Layer Network Diagnostics

import platform
import socket
import subprocess
import re
import time
import ssl
import urllib.request
import psutil
import dns.resolver

OK = "OK"
WARN = "WARNING"
FAIL = "FAILED"

LAYER_NAMES = {
    1: "Physical",
    2: "Data Link",
    3: "Network",
    4: "Transport",
    5: "Session",
    6: "Presentation",
    7: "Application"
}


def result(layer, name, status, detail, value=None):
    return {
        "layer": layer,
        "name": name,
        "status": status,
        "detail": detail,
        "value": value
    }


# --------------------------------------------------
# LAYER 1 - PHYSICAL / INTERFACE STATUS
# --------------------------------------------------

def check_l1():
    interfaces = psutil.net_if_stats()
    active = [
        name for name, stats in interfaces.items()
        if stats.isup and not name.lower().startswith("lo")
    ]

    if not active:
        return [
            result(1, "Network Interface", FAIL,
                   "No active network interface detected")
        ]

    wifi = next(
        (name for name in active if "wi-fi" in name.lower()
         or "wifi" in name.lower()),
        active[0]
    )

    stats = interfaces[wifi]

    return [
        result(
            1, "Network Interface", OK,
            f"{wifi} is active; reported link speed: "
            f"{stats.speed or 'unknown'} Mbps"
        )
    ]


# --------------------------------------------------
# NETWORK INFORMATION - WINDOWS GATEWAY FIX
# --------------------------------------------------

def get_network_info():
    hostname = socket.gethostname()
    local_ip = "Unavailable"
    gateway = None

    if platform.system() == "Windows":
        try:
            command = [
                "powershell", "-NoProfile", "-Command",
                (
                    "$cfg = Get-NetIPConfiguration "
                    "-InterfaceAlias 'Wi-Fi' "
                    "-ErrorAction SilentlyContinue; "
                    "if ($cfg) { "
                    "'IP=' + $cfg.IPv4Address.IPAddress; "
                    "'GW=' + $cfg.IPv4DefaultGateway.NextHop "
                    "}"
                )
            ]

            output = subprocess.run(
                command, capture_output=True, text=True, timeout=8
            ).stdout

            for line in output.splitlines():
                if line.startswith("IP=") and line[3:].strip():
                    local_ip = line[3:].strip()
                elif line.startswith("GW=") and line[3:].strip():
                    gateway = line[3:].strip()

        except (OSError, subprocess.TimeoutExpired):
            pass

    # Fallback: determine the source IP used for outbound traffic
    if local_ip == "Unavailable":
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("1.1.1.1", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
        except OSError:
            pass

    return {
        "Hostname": hostname,
        "Local IP": local_ip,
        "Default Gateway": gateway
    }


# --------------------------------------------------
# COMMON CONNECTIVITY TESTS
# --------------------------------------------------

def ping_test(host, count=5):
    command = (
        ["ping", "-n", str(count), "-w", "1500", host]
        if platform.system() == "Windows"
        else ["ping", "-c", str(count), "-W", "2", host]
    )

    try:
        completed = subprocess.run(
            command, capture_output=True, text=True,
            timeout=count * 3 + 5
        )

        output = completed.stdout + completed.stderr

        times = [
            float(value)
            for value in re.findall(
                r"time[=<]\s*([\d.]+)\s*ms",
                output, re.IGNORECASE
            )
        ]

        loss = round((count - len(times)) / count * 100, 1)
        average = round(sum(times) / len(times), 2) if times else None

        jitter = None
        if len(times) >= 2:
            differences = [
                abs(times[i] - times[i - 1])
                for i in range(1, len(times))
            ]
            jitter = round(sum(differences) / len(differences), 2)

        return {
            "status": (
                FAIL if not times
                else WARN if loss > 0 or average > 150
                else OK
            ),
            "latency_ms": average,
            "packet_loss": loss,
            "jitter_ms": jitter,
            "details": (
                f"{host}: average={average} ms, "
                f"loss={loss}%, jitter={jitter} ms"
                if times else f"No ping replies from {host}"
            )
        }

    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": WARN,
            "latency_ms": None,
            "packet_loss": None,
            "jitter_ms": None,
            "details": f"Ping test unavailable: {error}"
        }


def tcp_test(host, port=443):
    start = time.perf_counter()

    try:
        with socket.create_connection((host, port), timeout=5):
            elapsed = (time.perf_counter() - start) * 1000

        return result(
            4, "TCP Connection", OK,
            f"{host}:{port} connected in {elapsed:.2f} ms",
            round(elapsed, 2)
        )

    except OSError as error:
        return result(
            4, "TCP Connection", WARN,
            f"Connection to {host}:{port} failed: {error}"
        )


# --------------------------------------------------
# LAYER 2 - DATA LINK / ARP
# --------------------------------------------------

def check_l2(gateway):
    if not gateway:
        return [
            result(2, "Gateway ARP", WARN,
                   "No Wi-Fi gateway detected; ARP check skipped")
        ]

    # Ping is attempted to help populate the local ARP table.
    # A failed ping does not itself prove ARP has failed.
    if platform.system() == "Windows":
        try:
            subprocess.run(
                ["ping", "-n", "1", "-w", "800", gateway],
                capture_output=True, text=True, timeout=3
            )
            output = subprocess.run(
                ["arp", "-a", gateway],
                capture_output=True, text=True, timeout=3
            ).stdout

            mac = re.search(
                r"([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})",
                output
            )

            if mac:
                return [
                    result(
                        2, "Gateway ARP", OK,
                        f"Gateway {gateway} has MAC address "
                        f"{mac.group(1)}"
                    )
                ]

        except (OSError, subprocess.TimeoutExpired):
            pass

    return [
        result(
            2, "Gateway ARP", WARN,
            "No gateway MAC address was found in the ARP lookup. "
            "The entry may be missing or unavailable."
        )
    ]


# --------------------------------------------------
# LAYER 3 - NETWORK / IP AND ROUTING
# --------------------------------------------------

def check_l3(info):
    output = []

    if info["Local IP"] == "Unavailable":
        output.append(
            result(3, "Local IP", FAIL,
                   "Could not determine the local IP address")
        )
    else:
        output.append(
            result(3, "Local IP", OK, info["Local IP"])
        )

    if info["Default Gateway"]:
        output.append(
            result(
                3, "Default Gateway", OK,
                info["Default Gateway"]
            )
        )

        gateway_ping = ping_test(info["Default Gateway"])

        # A failed ICMP test is a warning, not definitive proof
        # that the gateway or route is down.
        gateway_status = (
            WARN if gateway_ping["status"] == FAIL
            else gateway_ping["status"]
        )

        output.append(
            result(
                3, "Gateway Ping", gateway_status,
                gateway_ping["details"],
                gateway_ping["latency_ms"]
            )
        )
    else:
        output.append(
            result(3, "Default Gateway", WARN,
                   "Wi-Fi default gateway was not detected")
        )

    internet_ping = ping_test("1.1.1.1")

    output.append(
        result(
            3, "Internet Ping", internet_ping["status"],
            internet_ping["details"],
            internet_ping["latency_ms"]
        )
    )

    return output, internet_ping


# --------------------------------------------------
# LAYER 4 - TRANSPORT / TCP
# --------------------------------------------------

def check_l4():
    return [tcp_test("1.1.1.1", 443)]


# --------------------------------------------------
# LAYER 5 - SESSION / TLS HANDSHAKE
# --------------------------------------------------

def check_l5():
    host = "example.com"

    try:
        raw = socket.create_connection((host, 443), timeout=5)
        context = ssl.create_default_context()

        start = time.perf_counter()
        secure = context.wrap_socket(raw, server_hostname=host)
        elapsed = (time.perf_counter() - start) * 1000
        secure.close()

        status = WARN if elapsed > 500 else OK

        return [
            result(
                5, "TLS Session Setup", status,
                f"Secure session established in {elapsed:.2f} ms",
                round(elapsed, 2)
            )
        ]

    except (OSError, ssl.SSLError) as error:
        return [
            result(
                5, "TLS Session Setup", WARN,
                f"Secure session could not be established: {error}"
            )
        ]


# --------------------------------------------------
# LAYER 6 - PRESENTATION / TLS AND CERTIFICATE
# --------------------------------------------------

def check_l6():
    host = "example.com"

    try:
        context = ssl.create_default_context()

        with socket.create_connection((host, 443), timeout=5) as raw:
            with context.wrap_socket(
                raw, server_hostname=host
            ) as secure:
                version = secure.version()
                cipher = secure.cipher()[0]
                certificate = secure.getpeercert()

        expiry_text = certificate.get("notAfter")
        expiry = ssl.cert_time_to_seconds(expiry_text)
        days_left = int((expiry - time.time()) / 86400)

        status = (
            FAIL if days_left <= 0
            else WARN if days_left <= 14
            else OK
        )

        return [
            result(
                6, "TLS Version and Cipher", OK,
                f"{version}; cipher: {cipher}"
            ),
            result(
                6, "Certificate Validity", status,
                f"Certificate expires in approximately {days_left} days"
            )
        ]

    except (OSError, ssl.SSLError, KeyError, ValueError) as error:
        return [
            result(
                6, "TLS Certificate", WARN,
                f"Certificate details unavailable: {error}"
            )
        ]


# --------------------------------------------------
# LAYER 7 - APPLICATION / DNS AND HTTPS
# --------------------------------------------------

def check_l7():
    output = []
    hostname = "example.com"

    # System DNS lookup
    start = time.perf_counter()

    try:
        socket.getaddrinfo(hostname, 443)
        elapsed = (time.perf_counter() - start) * 1000

        output.append(
            result(
                7, "DNS Lookup",
                WARN if elapsed > 500 else OK,
                f"{hostname} resolved in {elapsed:.2f} ms",
                round(elapsed, 2)
            )
        )

    except OSError as error:
        output.append(
            result(
                7, "DNS Lookup", WARN,
                f"System DNS lookup failed: {error}"
            )
        )

    # HTTPS application request
    start = time.perf_counter()

    try:
        request = urllib.request.Request(
            "https://example.com",
            method="GET"
        )

        with urllib.request.urlopen(request, timeout=8) as response:
            elapsed = (time.perf_counter() - start) * 1000
            status_code = response.status

        output.append(
            result(
                7, "HTTPS Request",
                OK if status_code == 200 else WARN,
                f"HTTP status {status_code}; "
                f"response time {elapsed:.2f} ms",
                round(elapsed, 2)
            )
        )

    except Exception as error:
        output.append(
            result(
                7, "HTTPS Request", WARN,
                f"HTTPS request failed: {error}"
            )
        )

    return output


# --------------------------------------------------
# RUN ALL LAYER CHECKS
# --------------------------------------------------

def run_all():
    info = get_network_info()

    l1 = check_l1()
    l2 = check_l2(info["Default Gateway"])
    l3, internet_ping = check_l3(info)
    l4 = check_l4()
    l5 = check_l5()
    l6 = check_l6()
    l7 = check_l7()

    results = l1 + l2 + l3 + l4 + l5 + l6 + l7

    return info, results, internet_ping


# --------------------------------------------------
# DIAGNOSIS SUMMARY
# --------------------------------------------------


def summarize(results):
    """Generate an evidence-based network diagnosis."""
    health = {}

    for layer in range(1, 8):
        layer_checks = [
            item for item in results
            if item.get("layer") == layer
        ]

        if not layer_checks:
            health[layer] = None
        elif any(item.get("status") == FAIL for item in layer_checks):
            health[layer] = FAIL
        elif any(item.get("status") == WARN for item in layer_checks):
            health[layer] = WARN
        else:
            health[layer] = OK

    by_name = {item["name"]: item for item in results}

    def status(name):
        item = by_name.get(name)
        return item.get("status") if item else None

    gateway = status("Gateway Ping")
    internet = status("Internet Ping")
    interface = status("Network Interface")
    local_ip = status("Local IP")
    tcp = status("TCP Connection")
    tls = status("TLS Session Setup")
    https = status("HTTPS Request")
    dns = status("DNS Lookup")
    cert = status("Certificate Validity")

    # Evidence that application traffic can reach the internet.
    internet_works = tcp == OK or https == OK

    # 1. Local interface and IP configuration.
    if interface == FAIL:
        return health, (
            "Local interface problem: no active network interface "
            "was detected. Check the Wi-Fi or Ethernet adapter."
        )

    if local_ip == FAIL:
        return health, (
            "Local IP configuration problem: the local IP address "
            "could not be determined. Check the adapter and DHCP."
        )

    # 2. Certificate expiry is specific evidence, if this check ran.
    if cert == FAIL:
        item = by_name["Certificate Validity"]
        return health, (
            f"Certificate validity problem: {item['detail']} "
            "Verify the system date and certificate details."
        )

    # 3. Successful external traffic takes precedence over failed ping.
    if internet_works:
        if gateway in (WARN, FAIL):
            return health, (
                "External connectivity is working, but the gateway "
                "did not respond reliably to ping. ICMP filtering or "
                "gateway response behavior may explain this. A "
                "gateway ping failure alone does not prove an outage."
            )

        if internet == FAIL:
            return health, (
                "TCP or HTTPS connectivity succeeded, but internet "
                "ping failed. ICMP filtering or destination-specific "
                "behavior is possible; basic application connectivity "
                "is still available."
            )

    # 4. Several independent connectivity failures suggest a wider issue.
    external_checks = [internet, tcp, https]
    failed_external = sum(
        value in (WARN, FAIL) for value in external_checks
    )

    if failed_external >= 2:
        return health, (
            "Possible connectivity or routing problem: multiple "
            "external checks reported problems. Check the default "
            "route, firewall, VPN configuration and destination "
            "availability. Repeat the tests before confirming a cause."
        )

    # 5. DNS diagnosis: interpret alongside HTTPS results.
    if dns in (WARN, FAIL):
        if https == OK:
            return health, (
                "DNS lookup reported a problem, but HTTPS succeeded. "
                "The checks may use different resolution paths or "
                "destinations. Repeat DNS testing before concluding "
                "that name resolution is unavailable."
            )

        return health, (
            "Possible DNS resolution problem. Retry the lookup and "
            "test another hostname. If IP-based connectivity works, "
            "investigate the configured DNS resolver."
        )

    # 6. TLS issues are more meaningful when TCP works.
    if tls in (WARN, FAIL) and tcp == OK:
        return health, (
            "TCP connectivity succeeded, but TLS session setup "
            "reported a problem. Check certificate trust, system "
            "time, proxy behavior and the destination service."
        )

    # 7. HTTPS issue despite successful TCP.
    if https in (WARN, FAIL) and tcp == OK:
        return health, (
            "TCP connectivity succeeded, but the HTTPS request "
            "reported a problem. Inspect the HTTP status or error, "
            "TLS settings, proxy configuration and destination."
        )

    # 8. Latency and packet loss indicate performance, not necessarily outage.
    ping_item = by_name.get("Internet Ping")
    if ping_item:
        latency = ping_item.get("value")
        detail = str(ping_item.get("detail", "")).lower()

        if ping_item.get("status") == WARN:
            return health, (
                "Possible network performance issue: internet ping "
                "reported a warning. Repeat the measurement and "
                "compare latency and packet loss before identifying "
                "a root cause."
            )

    # 9. Report remaining checks without inventing a root cause.
    failures = [
        item for item in results
        if item.get("status") == FAIL
    ]
    warnings = [
        item for item in results
        if item.get("status") == WARN
    ]

    if failures:
        item = failures[0]
        return health, (
            f"Diagnostic check failed: {item['name']} "
            f"(Layer {item['layer']}). {item['detail']} "
            "Use the other results to narrow down the cause."
        )

    if warnings:
        item = warnings[0]
        return health, (
            f"Further investigation recommended: {item['name']} "
            f"(Layer {item['layer']}). {item['detail']} "
            "This result alone does not establish the root cause."
        )

    # Missing checks must not be described as successful checks.
    expected = [
        "Network Interface", "Local IP", "Internet Ping",
        "TCP Connection", "TLS Session Setup",
        "DNS Lookup", "HTTPS Request"
    ]
    missing = [name for name in expected if name not in by_name]

    if missing:
        return health, (
            "Diagnosis is incomplete because these checks were "
            "not returned: " + ", ".join(missing) + "."
        )

    return health, (
        "All tested network checks passed. No immediate issue "
        "was detected for the tested interface and destinations."
    )



if __name__ == "__main__":
    info, results, internet_ping = run_all()
    health, verdict = summarize(results)

    print("NETWORK INFORMATION")
    for key, value in info.items():
        print(f"{key}: {value}")

    print("\nLAYER-BY-LAYER RESULTS")
    for item in results:
        print(
            f"L{item['layer']} [{item['status']}] "
            f"{item['name']}: {item['detail']}"
        )

    print("\nFINAL DIAGNOSIS")
    print(verdict)
