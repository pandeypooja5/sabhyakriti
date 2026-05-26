#!/bin/bash

echo "🔍 Verifying Sabhyakriti APIs..."
echo ""

BASE_URL="https://sabhyakriti.com"

# Test endpoints
declare -a endpoints=(
  "/api/v1/products"
  "/api/v1/categories"
  "/api/v1/cart"
  "/api/v1/orders"
  "/api/v1/payments"
)

echo "Testing API endpoints:"
for endpoint in "${endpoints[@]}"; do
  response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")

  if [ "$response" = "200" ]; then
    echo "✅ $endpoint: $response (OK)"
  else
    echo "❌ $endpoint: $response (Expected 200)"
  fi
done

echo ""
echo "API verification complete!"
