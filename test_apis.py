#!/usr/bin/env python3
"""
Test all Sabhyakriti APIs to verify they're working correctly.
Tests both public endpoints and the frontend's ability to call them.
"""

import asyncio
import httpx
import json
from typing import Any

BASE_URL = "https://sabhyakriti.com"
API_BASE = f"{BASE_URL}/api/v1"

# API endpoints to test
ENDPOINTS = {
    "health_checks": [
        ("GET", "/api/v1/products/health", "Product Service Health"),
        ("GET", "/api/v1/cart/health", "Cart Service Health"),
        ("GET", "/api/v1/orders/health", "Order Service Health"),
        ("GET", "/api/v1/payments/health", "Payment Service Health"),
    ],
    "public_endpoints": [
        ("GET", "/api/v1/products", "List Products"),
        ("GET", "/api/v1/categories", "List Categories"),
    ],
    "auth_endpoints": [
        ("POST", "/api/v1/auth/register", "Register User", {"email": "test@example.com", "password": "Test@123", "first_name": "Test", "last_name": "User"}),
    ],
}

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.results = []
        self.tokens = {}

    async def setup(self):
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def teardown(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def test_endpoint(
        self,
        method: str,
        path: str,
        description: str,
        payload: dict | None = None,
        headers: dict | None = None
    ) -> dict[str, Any]:
        """Test a single endpoint."""
        url = f"{self.base_url}{path}"

        try:
            if method == "GET":
                response = await self.client.get(url, headers=headers or {})
            elif method == "POST":
                response = await self.client.post(
                    url,
                    json=payload,
                    headers=headers or {}
                )
            else:
                return {
                    "endpoint": description,
                    "method": method,
                    "path": path,
                    "status": "SKIPPED",
                    "error": f"Unsupported method: {method}"
                }

            # Check for success
            is_success = 200 <= response.status_code < 300

            result = {
                "endpoint": description,
                "method": method,
                "path": path,
                "status": "PASS" if is_success else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }

            # Try to parse JSON response
            try:
                result["response_preview"] = response.json()
            except:
                result["response_preview"] = response.text[:200]

            # Extract token if available (for auth endpoints)
            if is_success and "token" in response.text.lower():
                try:
                    data = response.json()
                    if "access_token" in data:
                        self.tokens["access_token"] = data["access_token"]
                except:
                    pass

            return result

        except httpx.ConnectError as e:
            return {
                "endpoint": description,
                "method": method,
                "path": path,
                "status": "ERROR",
                "error": f"Connection failed: {e}"
            }
        except httpx.TimeoutException as e:
            return {
                "endpoint": description,
                "method": method,
                "path": path,
                "status": "ERROR",
                "error": f"Timeout: {e}"
            }
        except Exception as e:
            return {
                "endpoint": description,
                "method": method,
                "path": path,
                "status": "ERROR",
                "error": str(e)
            }

    async def run_all_tests(self):
        """Run all API tests."""
        print("=" * 80)
        print("SABHYAKRITI API TEST SUITE")
        print("=" * 80)
        print(f"\nTesting: {self.base_url}\n")

        # Test health checks first
        print("1. HEALTH CHECKS")
        print("-" * 80)
        for method, path, description in ENDPOINTS["health_checks"]:
            result = await self.test_endpoint(method, path, description)
            self.results.append(result)
            status_symbol = "[OK]" if result["status"] == "PASS" else "[FAIL]"
            print(f"  {status_symbol} {result['endpoint']:<40} [{result['status']}] {result.get('status_code', 'N/A')}")

        # Test public endpoints
        print("\n2. PUBLIC ENDPOINTS (No Auth Required)")
        print("-" * 80)
        for method, path, description in ENDPOINTS["public_endpoints"]:
            result = await self.test_endpoint(method, path, description)
            self.results.append(result)
            status_symbol = "[OK]" if result["status"] == "PASS" else "[FAIL]"
            print(f"  {status_symbol} {result['endpoint']:<40} [{result['status']}] {result.get('status_code', 'N/A')}")

        # Test auth endpoints
        print("\n3. AUTHENTICATION ENDPOINTS")
        print("-" * 80)
        for endpoint in ENDPOINTS["auth_endpoints"]:
            if len(endpoint) == 4:
                method, path, description, payload = endpoint
            else:
                method, path, description = endpoint
                payload = None

            result = await self.test_endpoint(method, path, description, payload)
            self.results.append(result)
            status_symbol = "[OK]" if result["status"] == "PASS" else "[FAIL]"
            print(f"  {status_symbol} {result['endpoint']:<40} [{result['status']}] {result.get('status_code', 'N/A')}")

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        total = len(self.results)

        print(f"\nTotal Tests:   {total}")
        print(f"Passed:        {passed}")
        print(f"Failed:        {failed}")
        print(f"Errors:        {errors}")

        if failed > 0:
            print("\nFailed Endpoints:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['endpoint']} (HTTP {result.get('status_code')})")

        if errors > 0:
            print("\nEndpoints with Errors:")
            for result in self.results:
                if result["status"] == "ERROR":
                    print(f"  - {result['endpoint']}: {result.get('error')}")

        print("\n" + "=" * 80)

        # Overall result
        if failed == 0 and errors == 0:
            print("RESULT: ALL TESTS PASSED!")
        elif errors > 0:
            print("RESULT: SOME ENDPOINTS UNREACHABLE (Check deployment)")
        else:
            print("RESULT: SOME ENDPOINTS FAILED (Check API responses)")

        print("=" * 80 + "\n")


async def main():
    """Main test runner."""
    tester = APITester()
    await tester.setup()
    try:
        await tester.run_all_tests()
    finally:
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())
