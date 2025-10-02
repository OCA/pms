# PMS Downpayment Auto-Invoicing

Automates **downpayment (advance) invoicing** for PMS payments, **per company** configuration.

## What it does

- Adds a **“Downpayment Automation”** tab on the *Company* form.
- Lets you enable automatic downpayment invoicing and choose a **schedule**:
  - **Daily** (every day)
  - **Weekly** (on a chosen weekday)
  - **Monthly** (on first/last/penultimate or a fixed day 1..28)
  - **Quarterly** (on the **last day of each quarter**: Mar 31, Jun 30, Sep 30, Dec 31)
- A single **cron job with no parameters** runs daily and, for each company enabled:

  - Decides if it **should run today** based on that company’s schedule.
  - Computes a **time window** `(last theoretical run, today]`.
  - Selects **payments** with posted moves in that window, linked to folios with `last_checkout > today`,
    and **not already invoiced** as downpayments.

## Business logic recap

- A payment is considered a *downpayment candidate* if:
  - Its accounting move is **posted** within the computed window.
  - The journal is **not** marked *avoid_auto_invoice_downpayment*.
  - It is linked to at least one folio and **at least one** linked folio has `last_checkout > today`.
  - It has **no reconciled downpayment invoice yet**.

> This module does **not** change your existing downpayment definition. It only automates the invoicing workflow based on timing rules.

## Configuration

Open **Settings → Companies → Your Company → Downpayment Automation**:
- **Enable Auto Downpayment Invoicing**
- **Schedule Mode**: daily, weekly, monthly, quarterly
- **Weekly Day** (if weekly)
- **Monthly Marker & Day** (if monthly)
- **Batch Size** (performance control)

## Notes

- The cron runs daily at a fixed time, but **the method decides** whether it should act for each company based on its schedule.
- Multi-company aware: the process runs **per company** and uses each company’s configuration.
