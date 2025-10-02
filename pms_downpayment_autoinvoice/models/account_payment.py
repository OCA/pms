import calendar
import logging
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # ------------------------------
    # Main cron entry (no arguments)
    # ------------------------------
    @api.model
    def pms_run_downpayment_autoinvoice_cron(self):
        """
        Daily cron with no arguments.
        For each company with automation enabled, evaluate
        schedule and run auto-invoicing if due.
        """
        companies = self.env["res.company"].search(
            [("downpayment_auto_enabled", "=", True)]
        )
        today = fields.Date.context_today(self)
        _logger.info(
            "Downpayment cron: evaluating %s companies on %s",
            len(companies),
            today,
        )

        # Fallback partner once
        try:
            fallback_partner = self.env.ref("pms.various_pms_partner")
        except ValueError:
            fallback_partner = False

        for company in companies:
            # Work in company context
            self_company = self.with_company(company)

            mode = (company.downpayment_auto_mode or "monthly").strip().lower()
            batch_size = company.downpayment_auto_batch_size or 200

            # Resolve value by mode
            if mode == "weekly":
                value = (company.downpayment_auto_weekday or "").strip().lower()
            elif mode == "monthly":
                marker = company.downpayment_auto_monthly_marker or "last"
                if marker == "fixed":
                    value = int(company.downpayment_auto_monthly_day or 1)
                else:
                    value = marker
            else:
                value = None  # quarterly ignores value

            # Decide whether to run
            try:
                should_run = self_company._should_run_today(mode, value, today)
            except Exception as exc:
                _logger.exception(
                    "Company %s schedule evaluation failed: %s",
                    company.name,
                    exc,
                )
                continue

            if not should_run:
                _logger.info(
                    "Company %s: skip (mode=%s, value=%s)",
                    company.name,
                    mode,
                    value,
                )
                continue

            # Compute window
            try:
                win_start, win_end = self_company._compute_window(mode, value, today)
            except Exception as exc:
                _logger.exception(
                    "Company %s window computation failed: %s",
                    company.name,
                    exc,
                )
                continue

            _logger.info(
                "Company %s: running downpayment auto-invoicing window %s..%s "
                "(mode=%s, value=%s, batch=%s)",
                company.name,
                win_start,
                win_end,
                mode,
                value,
                batch_size,
            )

            # Candidates: posted moves in window, allowed journal,
            # linked folios with checkout > today
            domain = [
                ("company_id", "=", company.id),
                ("move_id.state", "=", "posted"),
                ("move_id.journal_id.avoid_autoinvoice_downpayment", "=", False),
                ("folio_ids", "!=", False),
                ("move_id.date", ">=", win_start),
                ("move_id.date", "<=", win_end),
                ("folio_ids.last_checkout", ">", today),
            ]
            candidates = self_company.search(domain)
            pending = candidates.filtered(
                lambda p, sc=self_company: not sc._has_downpayment_invoice(p)
            )
            _logger.info(
                "Company %s: candidates=%s, pending=%s",
                company.name,
                len(candidates),
                len(pending),
            )

            ok = 0
            fail = 0

            def _iter_batches(recs, size):
                total = len(recs)
                for i in range(0, total, size):
                    yield recs[i : i + size]

            for batch in _iter_batches(pending, batch_size):
                for payment in batch:
                    partner = (
                        payment.partner_id
                        or fallback_partner
                        or payment.company_id.partner_id
                    )
                    if not partner:
                        _logger.warning(
                            "[SKIP] Company %s Payment %s: cannot resolve partner",
                            company.name,
                            payment.id,
                        )
                        fail += 1
                        continue
                    _logger.info(
                        "[DRY] Company %s Payment %s amount=%s partner='%s'",
                        company.name,
                        payment.id,
                        payment.amount,
                        partner.display_name,
                    )
                    ok += 1

                    with self.env.cr.savepoint():
                        try:
                            move = self_company._create_downpayment_invoice(
                                payment=payment,
                                partner_id=partner.id,
                            )
                            _logger.info(
                                "[OK] Company %s Payment %s -> invoice %s posted",
                                company.name,
                                payment.id,
                                move.id,
                            )
                            ok += 1
                        except Exception as e:
                            _logger.exception(
                                "[ERR] Company %s Payment %s: %s",
                                company.name,
                                payment.id,
                                e,
                            )
                            fail += 1

            _logger.info(
                "Company %s: finished ok=%s fail=%s",
                company.name,
                ok,
                fail,
            )

        return True

    # --------------------------
    # Scheduling/date utilities
    # --------------------------
    @api.model
    def _should_run_today(self, mode, value, ref_date):
        """
        Return True if the job should execute on ref_date.
        - daily: always true
        - weekly: run on the given weekday ('mon'..'sun' or 0..6)
        - monthly: run on day (first|last|penultimate|1..28)
        - quarterly: run on the LAST day of each quarter
                      (Mar 31, Jun 30, Sep 30, Dec 31)
        """
        ms = str(mode).strip().lower()
        if ms == "daily":
            return True
        if ms == "weekly":
            return ref_date.weekday() == self._weekday_from_value(value)
        if ms == "monthly":
            return ref_date.day == self._resolve_month_day(value, ref_date)
        if ms == "quarterly":
            return (ref_date.month, ref_date.day) in [
                (3, 31),
                (6, 30),
                (9, 30),
                (12, 31),
            ]
        raise ValueError("Unknown mode: %s" % mode)

    @api.model
    def _compute_window(self, mode, value, ref_date):
        """
        Compute [start_date_inclusive, end_date_inclusive] as
        (last theoretical run, ref_date].
        Start is the day AFTER the last scheduled date <= ref_date.
        """
        ms = str(mode).strip().lower()
        if ms == "daily":
            return ref_date - relativedelta(days=1), ref_date
        if ms == "weekly":
            wd = self._weekday_from_value(value)
            delta = (ref_date.weekday() - wd) % 7
            last_sched = ref_date - relativedelta(days=delta)
            return last_sched + relativedelta(days=1), ref_date
        if ms == "monthly":
            day = self._resolve_month_day(value, ref_date)
            last_day_curr = calendar.monthrange(ref_date.year, ref_date.month)[1]
            cand = ref_date.replace(day=min(day, last_day_curr))
            if cand > ref_date:
                prev = ref_date.replace(day=1) - relativedelta(days=1)
                last_day_prev = calendar.monthrange(prev.year, prev.month)[1]
                cand = prev.replace(day=min(day, last_day_prev))
            return cand + relativedelta(days=1), ref_date
        if ms == "quarterly":
            # Window = (end of previous quarter, ref_date]
            q_months = [3, 6, 9, 12]
            prev_q_month = max([m for m in q_months if m <= ref_date.month])
            q_end = ref_date.replace(
                month=prev_q_month,
                day=calendar.monthrange(ref_date.year, prev_q_month)[1],
            )
            if q_end > ref_date:
                q_end = ref_date.replace(year=ref_date.year - 1, month=12, day=31)
            return q_end + relativedelta(days=1), ref_date
        raise ValueError("Unknown mode: %s" % mode)

    @api.model
    def _weekday_from_value(self, v):
        """Return 0..6 for Mon..Sun. Accepts 'mon'..'sun' or int 0..6."""
        if isinstance(v, int):
            return v
        m = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        return m[str(v).strip().lower()]

    @api.model
    def _resolve_month_day(self, value, ref_date):
        """
        Resolve monthly trigger to a concrete day number for ref_date's month.
        Accepts: 'first' | 'last' | 'penultimate' | int 1..28
        """
        if isinstance(value, int) and 1 <= value <= 28:
            return value
        value_s = str(value).strip().lower()
        last = calendar.monthrange(ref_date.year, ref_date.month)[1]
        if value_s == "first":
            return 1
        if value_s == "last":
            return last
        if value_s == "penultimate":
            return max(1, last - 1)
        raise ValueError("Invalid monthly value: %s" % value)

    # --------------------------------------
    # Business logic & invoice creation
    # --------------------------------------
    @api.model
    def _has_downpayment_invoice(self, payment):
        """
        Return True if the payment already has a reconciled 'downpayment' invoice.
        """
        return bool(
            payment.folio_ids
            and payment.reconciled_invoice_ids.filtered(
                lambda inv: inv._is_downpayment()
            )
        )

    @api.model
    def _create_downpayment_invoice(self, payment, partner_id):
        """
        Create a downpayment invoice for the given payment and reconcile it.
        """
        invoice_wizard = self.env["folio.advance.payment.inv"].create(
            {
                "partner_invoice_id": partner_id,
                "advance_payment_method": "fixed",
                "fixed_amount": payment.amount,
            }
        )
        move = invoice_wizard.with_context(
            active_ids=payment.folio_ids.ids,
            return_invoices=True,
        ).create_invoices()
        if payment.payment_type == "outbound":
            move.action_switch_invoice_into_refund_credit_note()
        move.action_post()
        # Reconcile invoice and payment move lines
        for invoice, payment_move in zip(move, payment.move_id, strict=True):
            group = defaultdict(list)
            for line in (invoice.line_ids + payment_move.line_ids).filtered(
                lambda r: not r.reconciled
            ):
                group[(line.account_id, line.currency_id)].append(line.id)
            for (account, _dummy), line_ids in group.items():
                if account.reconcile or account.account_type == "liquidity":
                    self.env["account.move.line"].browse(line_ids).reconcile()
        # Default recipient for subsequent folio sale lines
        for folio in payment.folio_ids:
            for sale_line in folio.sale_line_ids.filtered(
                lambda r: not r.default_invoice_to
            ):
                sale_line.default_invoice_to = move.partner_id.id
        return move
