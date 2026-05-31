# Functional Design Plan — Unit 4: Order Microservice
# sabhyakriti-order-service

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

Unit 4 owns: Order, OrderItem, Address, ReturnRequest entities.
Handles: full order lifecycle (PENDING→CONFIRMED→SHIPPED→DELIVERED), address management,
order cancellation, return/refund requests, PDF invoice generation, notifications
(delegates to Notification Service), internal stock coordination with Product Service.
Requirements: FR-CART-06–10, FR-ORD-01–09, FR-ACC-02–05, FR-ADM-07, FR-ADM-09.

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
What is the return window — how many days after delivery can a customer initiate a return?

A) 7 days after delivery
B) 14 days after delivery
C) 30 days after delivery
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
For online paid orders (Razorpay/UPI) that are cancelled or returned — what is the refund timeline communicated to the customer?

A) 5–7 business days (standard bank processing time)
B) 3–5 business days
C) Instant refund to original payment source (within minutes via Razorpay instant refund)
D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 3
Can customers make a partial return (return some items from a multi-item order)?

A) Yes — customer selects which specific items to return
B) No — return must be for the entire order only
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
What should the PDF invoice include?

A) Standard GST invoice — seller details, GSTIN, buyer details, itemised list with HSN code, taxable amount, GST (5%), total, invoice number
B) Simplified receipt — order number, items, amounts, no GSTIN/HSN codes required
C) Other (please describe after [Answer]: tag below)

[Answer]: A