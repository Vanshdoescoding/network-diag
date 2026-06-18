import subprocess
import re 
from statistics import mean 

TARGETS = [
    "1.1.1.1", 
    "8.8.8.8", 
    "cloudflare.com",
    "google.com",
    "unsw.edu.au" 
]

WEIGHTS = {
    "latency": 1.0, 
    "jitter": 2.0,
    "loss": 10.0
}

# so  now we need to learn how to figure out the latency and pings and such. 

def run_ping(target, count = 10):
    command = ["ping", "-n", str(count), target]

    result = subprocess.run(
        command,
        capture_output = True, 
        text = True
    )

    return result.stdout

def extract_ping_times(output):
    """
    Extracts ping times like:
    time=12ms
    time<1ms
    """
    matches = re.findall(r"time[=<](\d+)ms", output)
    return [int(x) for x in matches]
    
def extract_packet_loss(output):
    """
    Extracts packet loss like:
    (0% loss)
    """
    match = re.search(r"\((\d+)% loss\)", output)

    if match:
        return int(match.group(1))

    return 100

def calculate_jitter(times):

    if len(times) < 2:
        return 0
    
    differences = []
    for i in range (1, len(times)):
        differences.append(abs(times[i] - times[i-1]))

    return mean(differences)

def calculate_cost(avg_latency, jitter, packet_loss):
    return (
        WEIGHTS["latency"] * avg_latency
        + WEIGHTS["jitter"] * jitter
        + WEIGHTS["loss"] * packet_loss
    )
def analyse_target(target):
    print(f"\nMeasuring {target}...")

    output = run_ping(target)
    times = extract_ping_times(output)
    packet_loss = extract_packet_loss(output)

    if not times:
        return {
            "target": target,
            "status": "failed",
            "avg_latency": None,
            "jitter": None,
            "packet_loss": packet_loss,
            "cost": float("inf")
        }

    avg_latency = mean(times)
    jitter = calculate_jitter(times)
    cost = calculate_cost(avg_latency, jitter, packet_loss)

    return {
        "target": target,
        "status": "ok",
        "avg_latency": avg_latency,
        "jitter": jitter,
        "packet_loss": packet_loss,
        "cost": cost
    }


def main():
    results = []

    for target in TARGETS:
        result = analyse_target(target)
        results.append(result)
    results.sort(key = lambda x: x["cost"])

    print("\n==============================")
    print("FlowPilot Scout Results")
    print("==============================")

    for result in results:
        if result["status"] == "failed":
            print(f"\n{result['target']}")
            print("Status: failed")
            print(f"Packet loss: {result['packet_loss']}%")
            continue

        print(f"\n{result['target']}")
        print(f"Average latency: {result['avg_latency']:.2f} ms")
        print(f"Jitter: {result['jitter']:.2f} ms")
        print(f"Packet loss: {result['packet_loss']}%")
        print(f"Network cost: {result['cost']:.2f}")

    best = results[0]

    print("\n==============================")
    print("Best target by network quality")
    print("==============================")
    print(best["target"])


if __name__ == "__main__":
    main()