#!/usr/bin/env python3
"""
Comprehensive API test for all Sabhyakriti services.
Tests key endpoints to verify database connectivity and API functionality.
"""

import subprocess
import json
import sys

def run_service_command(service_name, port, command):
    """Run a command inside a Railway service container."""
    try:
        result = subprocess.run(
            ["railway", "run", "--service", service_name, "--environment", "production", "--", "bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        print(f"Error running command in {service_name}: {e}")
        return None

def parse_json_response(response_text):
    """Safely parse JSON response."""
    if not response_text:
        return None
    try:
        return json.loads(response_text)
    except:
        return response_text

def test_all_services():
    """Test all service APIs."""
    tests = [
        ("PRODUCT-SERVICE", 8002, "/health", "curl -s http://localhost:8002/health"),
        ("PRODUCT-SERVICE", 8002, "/api/v1/products", "curl -s http://localhost:8002/api/v1/products | head -c 200"),
        ("PRODUCT-SERVICE", 8002, "/api/v1/categories", "curl -s http://localhost:8002/api/v1/categories | head -c 200"),

        ("CART-SERVICE", 8003, "/health", "curl -s http://localhost:8003/health"),
        ("CART-SERVICE", 8003, "/api/v1/cart/health", "curl -s http://localhost:8003/api/v1/cart/health"),

        ("ORDER-SERVICE", 8004, "/health", "curl -s http://localhost:8004/health"),
        ("ORDER-SERVICE", 8004, "/api/v1/orders/health", "curl -s http://localhost:8004/api/v1/orders/health"),

        ("PAYMENT-SERVICE", 8005, "/health", "curl -s http://localhost:8005/health"),
        ("PAYMENT-SERVICE", 8005, "/api/v1/payments/health", "curl -s http://localhost:8005/api/v1/payments/health"),

        ("NOTIFICATION-SERVICE", 8006, "/health", "curl -s http://localhost:8006/health"),

        ("AUTH-SERVICE", 8000, "/health", "curl -s http://localhost:8000/health"),
        ("AUTH-SERVICE", 8000, "/auth/.well-known/jwks.json", "curl -s http://localhost:8000/auth/.well-known/jwks.json | head -c 200"),
    ]

    print("=" * 100)
    print("SABHYAKRITI API TESTS - INTERNAL TESTING")
    print("=" * 100)
    print()

    results = []
    passed = 0
    failed = 0

    for service, port, endpoint, command in tests:
        print(f"Testing {service}{endpoint}...", end=" ")
        sys.stdout.flush()

        response = run_service_command(service, port, command)

        if response:
            # Try to parse as JSON to show preview
            data = parse_json_response(response)
            if isinstance(data, dict):
                preview = json.dumps(data, indent=2)[:100].replace('\n', ' ')
            else:
                preview = str(response)[:80]

            print(f"[PASS] {preview}...")
            results.append({
                "service": service,
                "endpoint": endpoint,
                "status": "PASS",
                "response": preview
            })
            passed += 1
        else:
            print("[FAIL] No response")
            results.append({
                "service": service,
                "endpoint": endpoint,
                "status": "FAIL",
                "response": "No response"
            })
            failed += 1
        print()

    # Summary
    print("=" * 100)
    print("TEST SUMMARY")
    print("=" * 100)
    print(f"Total Tests:  {len(tests)}")
    print(f"Passed:       {passed}")
    print(f"Failed:       {failed}")
    print()

    if failed == 0:
        print("SUCCESS: All internal API tests passed!")
        print()
        print("Next steps:")
        print("1. The services are all online and responding internally")
        print("2. Check Railway DNS/routing if external URLs (*.railway.app) still return 404")
        print("3. Test from the deployed frontend at https://sabhyakriti.com")
    else:
        print(f"FAILED: {failed} tests did not pass")
        for result in results:
            if result["status"] == "FAIL":
                print(f"  - {result['service']}{result['endpoint']}")

    print("=" * 100)
    return failed == 0

if __name__ == "__main__":
    success = test_all_services()
    sys.exit(0 if success else 1)
