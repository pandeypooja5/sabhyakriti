# Functional Design Plan — Unit 3: Cart & Wishlist Microservice
# sabhyakriti-cart-service

---

## Execution Checklist

- [ ] Step 1: Answer business logic questions (user fills [Answer]: tags below)
- [ ] Step 2: Analyze answers for ambiguities
- [ ] Step 3: Generate domain-entities.md
- [ ] Step 4: Generate business-rules.md
- [ ] Step 5: Generate business-logic-model.md
- [ ] Step 6: Present for approval

---

## Context Summary

Unit 3 owns: Cart, CartItem, Wishlist, WishlistItem, Coupon entities.
Handles: cart CRUD, cart pricing (subtotal + discount + tax + shipping + total),
coupon validation and application, wishlist management, internal endpoint for
Order Service to read and clear cart at checkout.
Requirements: FR-CART-01 to FR-CART-10, FR-ACC-06, FR-ADM-10.

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
How should shipping charges be calculated?

A) Free shipping always — no shipping charges at all
B) Free above ₹999; ₹99 flat fee below ₹999 (before discounts)
C) Free above ₹1499; ₹149 flat fee below ₹1499 (before discounts)
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 2
Should GST (tax) be displayed separately in the cart, or are prices inclusive of GST?

A) Prices are GST-inclusive — show "Inclusive of all taxes" with no separate line item
B) Show GST (5% on sarees) as a separate line item — e.g., Subtotal ₹1000 + GST ₹50 = Total ₹1050
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
Should the cart expire if unused for a long period?

A) Cart persists indefinitely — never expires (simplest approach)
B) Cart items are cleared after 30 days of inactivity (last_updated_at > 30 days ago)
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4
Can a user apply multiple coupons at once, or only one at a time?

A) One coupon at a time — applying a new coupon replaces the existing one
B) Stack up to 2 coupons — one flat discount + one percentage discount simultaneously
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
When a coupon with PERCENTAGE type is applied, should there be a maximum discount cap?

A) Yes — cap at ₹500 maximum discount regardless of cart value
B) Yes — cap at ₹1000 maximum discount
C) No cap — full percentage discount applied to any cart value
D) Other (please describe after [Answer]: tag below)

[Answer]: C
