# Micro-SaaS validation

Product name: Kozphy Automated Financial Reporting.
Target price if a hosted product is built later: US$29 per month.
Nothing is hosted, billed, or scheduled in this repository.

## What would count as evidence

A person who already receives a transaction export agrees, in writing, to pay for a defined workbook. A polite reply, a profile view, or a planning assumption is not evidence.

## Manual service first

1. Ask the eight discovery questions in `UPWORK.md`.
2. Run the local pipeline on a file the person chooses to send.
3. Deliver the four outputs and the notice sheet.
4. Record the payment, fee, and refund in `revenue-dashboard.xlsx` only after money moves.
5. Stop if two consecutive paid trials ask for nothing beyond the local command.

## Hosted MVP, only after payment evidence

Do not buy hosting or turn on a paid API for this product until at least one paid manual engagement has finished and the buyer asks for a shared login. Before any real customer file reaches a server, the build needs a separate tenant per customer, an authenticated account, stored files outside the web root, a retention limit, and tests that one tenant cannot read another tenant's file. Those controls are absent today.

## Features that stay unbuilt

File upload, report history, scheduled processing, audit logs for a hosted service, and account management.
