# Safe simulated tests for NetDoctor

import ast
from pathlib import Path

from checks import OK, WARN, FAIL, summarize

# Load the recommendations function without starting Streamlit.
app_path = Path(__file__).with_name("app.py")
source = app_path.read_text(encoding="utf-8")
tree = ast.parse(source)

function_node = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "recommendations"
)

namespace = {"OK": OK, "WARN": WARN, "FAIL": FAIL}
exec(
    compile(ast.Module(body=[function_node], type_ignores=[]),
            str(app_path), "exec"),
    namespace,
)
recommendations = namespace["recommendations"]


def make_result(layer, name, status, detail="Simulated test result",
                value=None):
    return {
        "layer": layer,
        "name": name,
        "status": status,
        "detail": detail,
        "value": value,
    }


def base_results():
    return [
        make_result(1, "Network Interface", OK),
        make_result(2, "Gateway ARP", OK),
        make_result(3, "Local IP", OK),
        make_result(3, "Default Gateway", OK),
        make_result(3, "Gateway Ping", OK, value=8.0),
        make_result(3, "Internet Ping", OK, value=40.0),
        make_result(4, "TCP Connection", OK, value=35.0),
        make_result(5, "TLS Session Setup", OK, value=40.0),
        make_result(6, "TLS Version and Cipher", OK),
        make_result(6, "Certificate Validity", OK,
                    "Certificate expires in 60 days"),
        make_result(7, "DNS Lookup", OK, value=0.4),
        make_result(7, "HTTPS Request", OK,
                    "HTTP status 200", value=110.0),
    ]


def replace_status(results, name, status, detail=None):
    for item in results:
        if item["name"] == name:
            item["status"] = status
            if detail is not None:
                item["detail"] = detail
            return
    raise ValueError(f"Missing simulated check: {name}")


def run_case(title, results, ping):
    health, verdict = summarize(results)
    advice = recommendations(results, ping)

    print(f"\n{'=' * 60}")
    print(title)
    print("Diagnosis:", verdict)
    print("Layer health:", health)
    print("Recommendations:")
    for icon, heading, detail in advice:
        print(f"  {icon} {heading}: {detail}")

    return verdict, advice


# Test A: all checks healthy.
results = base_results()
run_case(
    "TEST A — Healthy connection",
    results,
    {"latency_ms": 40.0, "packet_loss": 0.0, "jitter_ms": 9.0},
)

# Test B: high jitter, without marking ping itself as failed.
results = base_results()
run_case(
    "TEST B — High jitter",
    results,
    {"latency_ms": 40.0, "packet_loss": 0.0, "jitter_ms": 38.75},
)

# Test C: gateway ping fails, but external TCP/HTTPS still works.
results = base_results()
replace_status(results, "Gateway Ping", WARN,
               "Simulated gateway ping failure")
run_case(
    "TEST C — Gateway ping warning",
    results,
    {"latency_ms": 40.0, "packet_loss": 0.0, "jitter_ms": 9.0},
)

# Test D: certificate has expired.
results = base_results()
replace_status(results, "Certificate Validity", FAIL,
               "Simulated certificate expiry")
run_case(
    "TEST D — Expired certificate",
    results,
    {"latency_ms": 40.0, "packet_loss": 0.0, "jitter_ms": 9.0},
)

print("\nAll four simulated scenarios executed.")
print("No real network settings were changed.")
