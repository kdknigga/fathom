# Pitfalls Research

**Domain:** Financial calculator web app (financing comparison with opportunity cost modeling)
**Researched:** 2026-03-10
**Confidence:** MEDIUM (based on well-established financial math and web app patterns; web search unavailable for verification)

## Critical Pitfalls

### Pitfall 1: Floating-Point Arithmetic in Financial Calculations

**What goes wrong:**
Using Python `float` for money calculations produces rounding errors that accumulate over loan terms. A 60-month amortization schedule computed with `float` can drift by several dollars from the correct total. Users who cross-check against their bank's amortization table will see different numbers and lose trust immediately.

**Why it happens:**
Developers default to `float` because it is simpler. IEEE 754 binary floating point cannot represent values like `0.01` exactly. Over hundreds of multiply-and-round operations in an amortization loop, errors compound.

**How to avoid:**
Use Python's `decimal.Decimal` with explicit precision for all monetary values. Set a calculation context (e.g., `decimal.getcontext().prec = 28`) and round to cents only at the final display step, not at intermediate steps. Alternatively, compute in integer cents and convert to dollars at display time. Either approach works; mixing them does not.

**Warning signs:**
- Amortization schedule final payment does not exactly zero out the remaining balance
- Two options with identical inputs produce True Total Cost values that differ by fractions of a cent
- Unit tests that compare expected dollar values with `==` fail intermittently

**Phase to address:**
Phase 1 (Calculation Engine) -- this must be the foundation. Retrofitting `Decimal` into a `float`-based engine requires touching every calculation.

---

### Pitfall 2: Wrong Comparison Period Normalization

**What goes wrong:**
When comparing a 24-month 0% promo against a 60-month loan, the app must normalize both to the same 60-month window. The common mistake is to stop modeling the 0% option at month 24 -- ignoring what happens to the freed-up monthly payments for months 25-60. This makes short-term options look artificially cheap because the opportunity cost of reinvested payments is omitted.

**Why it happens:**
Developers think "the loan is paid off, so the cost is final." But the whole point of this app is opportunity cost modeling. Cash freed up early must be modeled as invested for the remaining comparison period, or the comparison is not apples-to-apples.

**How to avoid:**
Define a clear "comparison window" equal to the longest term among active options. For each option that terminates early:
1. Calculate the monthly payment that was being made.
2. From termination month through end of comparison window, compound those monthly contributions at the user's investment return rate.
3. Subtract this investment gain from that option's True Total Cost (it reduces the effective cost).

Encode this as an explicit, tested step in the calculation pipeline -- not as an afterthought adjustment.

**Warning signs:**
- Cash purchase always "wins" when compared against short-term 0% financing (the opportunity cost of the lump sum is being ignored or understated)
- Changing comparison period length does not change relative rankings (it should, because it changes how long freed-up cash compounds)

**Phase to address:**
Phase 1 (Calculation Engine). The normalization logic is architecturally central. It cannot be bolted on later without rewriting the cost comparison pipeline.

---

### Pitfall 3: Deferred Interest Mismodeling

**What goes wrong:**
0% promotional financing with deferred interest is not the same as 0% financing. If the balance is not paid in full by the end of the promo period, interest is charged retroactively on the original balance from day one, often at 20-30% APR. Calculators that treat deferred interest as simply "0% for X months" dramatically understate the risk.

**Why it happens:**
The "happy path" (balance paid in full on time) is mathematically identical to true 0% financing. Developers model only the happy path because it is simpler. But the PRD explicitly includes a deferred interest toggle, meaning the app must communicate this risk.

**How to avoid:**
When the deferred interest flag is set:
1. Display a prominent caveat on the recommendation card explaining the retroactive interest risk.
2. Optionally calculate a "worst case" True Total Cost assuming the balance is not paid off in time, showing the user what happens if they miss the deadline.
3. Never present a deferred-interest option as equivalent to true 0% in the summary recommendation.

**Warning signs:**
- The recommendation card says "Take the 0% financing" without any caveat when deferred interest is enabled
- No unit tests covering the deferred-interest scenario
- The deferred interest toggle has no visible effect on displayed results

**Phase to address:**
Phase 1 (Calculation Engine) for the math, Phase 2 (Results Display) for the caveat UI.

---

### Pitfall 4: Opportunity Cost of Down Payments Ignored or Double-Counted

**What goes wrong:**
Down payments create opportunity cost (money paid upfront that could have been invested), but developers either forget to model it or accidentally count it twice -- once in the "total payments" column and again in the "opportunity cost" column.

**Why it happens:**
The down payment sits at the boundary between "money you paid" and "money you could have invested." The cash purchase is entirely a down payment (the full amount upfront). A loan with a down payment has both an upfront outlay and a stream of payments. Without a clear accounting framework, it is easy to lose track.

**How to avoid:**
Define a strict cost accounting model upfront:
- **Total Payments** = down payment + sum of all monthly payments
- **Opportunity Cost** = future value of down payment (compounded over comparison period) + future value of each monthly payment (compounded from payment date to end of comparison period) -- but only for the "what if you invested instead" counterfactual, which applies to the cash option
- For loan options, opportunity cost = future value of down payment only (monthly payments are obligatory, not discretionary cash)

The key insight: for a loan, the monthly payments are not "cash you could have invested" -- they are the cost of the loan. Only the down payment represents discretionary upfront cash. For the cash purchase, the entire purchase price is the upfront discretionary cash.

Document this accounting model explicitly in code comments and tests.

**Warning signs:**
- Cash purchase True Total Cost is exactly equal to purchase price (opportunity cost is missing)
- Loan with 50% down payment shows same opportunity cost as loan with 0% down payment
- True Total Cost for any option is negative (over-subtraction)

**Phase to address:**
Phase 1 (Calculation Engine). This is a design decision that must be made before any calculations are implemented.

---

### Pitfall 5: Month-Level vs. Annual Compounding Errors

**What goes wrong:**
The app must convert between annual rates (APR, investment return) and monthly calculations. Common errors: dividing annual rate by 12 for monthly rate (correct for APR, wrong for investment returns which compound differently), or mixing nominal and effective annual rates.

**Why it happens:**
APR is, by regulatory convention, a nominal annual rate divided by 12 for monthly calculations. But investment returns are typically quoted as effective annual rates. Using the same conversion formula for both produces wrong numbers.

**How to avoid:**
- For loan APR: monthly rate = APR / 12 (this is the regulatory standard)
- For investment returns: monthly rate = (1 + annual_rate)^(1/12) - 1 (converting effective annual to effective monthly)
- Label every rate variable in code with its type: `monthly_loan_rate`, `annual_effective_investment_rate`, etc.
- Write unit tests that verify a known amortization schedule (e.g., $10,000 at 5% APR for 36 months = $299.71/month)

**Warning signs:**
- Investment opportunity cost calculations are slightly but consistently off from manual spreadsheet verification
- Monthly payment calculation does not match standard amortization formula results
- Tests pass with round numbers but fail with realistic rates like 6.49%

**Phase to address:**
Phase 1 (Calculation Engine). Rate conversion must be correct from the start; it propagates into every other calculation.

---

### Pitfall 6: SVG Chart Accessibility as an Afterthought

**What goes wrong:**
Server-rendered SVG charts are generated without any semantic markup, ARIA attributes, or text alternatives. The charts look correct visually but are completely invisible to screen readers. Meeting WCAG 2.1 AA after the fact requires restructuring the SVG generation code.

**Why it happens:**
SVG is a visual format. Developers focus on making it look right and forget that `<svg>` elements are opaque to assistive technology by default. Unlike HTML tables which have inherent semantics, SVG has none unless explicitly added.

**How to avoid:**
From the first SVG chart implementation:
1. Add `role="img"` and `aria-labelledby` to the root `<svg>` element
2. Include a `<title>` and `<desc>` element inside the SVG with plain-text summary
3. Render an accessible data table alongside (or as a visually-hidden companion to) each chart
4. Use patterns/textures in addition to color to distinguish data series (not color-only)
5. Ensure all text in the SVG uses sufficient contrast ratios

**Warning signs:**
- SVG output contains no `<title>`, `<desc>`, or ARIA attributes
- Chart colors fail contrast checks against the background
- No companion data table exists for any chart
- Axe or Lighthouse accessibility audit flags chart elements

**Phase to address:**
Phase 2 (Charts/Visualization). Build accessibility into the SVG generation from the first implementation, not as a retrofit.

---

### Pitfall 7: HTMX Partial Updates Losing Form State

**What goes wrong:**
HTMX replaces a DOM fragment with server-rendered HTML. If the replacement target includes or overlaps the form, user inputs that were not submitted get wiped. The user types into field A, triggers a partial update on field B, and field A resets to its previous value.

**Why it happens:**
HTMX sends the form data in the request, but only the data from inputs that have names and are within the triggering form. If the server re-renders the entire form in the response, all inputs get replaced with the server's version of the state -- which may not include the user's latest keystrokes in other fields.

**How to avoid:**
- Use `hx-target` to replace only the results section, never the form itself
- If you must update form elements (e.g., showing/hiding conditional fields based on option type), use `hx-swap="outerHTML"` on the specific element, not the parent form
- Always echo back all form values in the server response so nothing is lost
- Use `hx-include` to explicitly include all form inputs in every request, even if they are outside the triggering element
- Test the "type in field A, change field B, verify field A retained" scenario explicitly

**Warning signs:**
- Users report "the form keeps resetting"
- Changing the option type dropdown clears previously entered values in other options
- Form state is inconsistent between what the user sees and what the server received

**Phase to address:**
Phase 2 (UI/HTMX Integration). Must be designed correctly in the HTMX wiring from the start.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `float` instead of `Decimal` for "just the prototype" | Faster initial development | Requires rewriting every calculation when precision bugs surface | Never -- start with `Decimal` from day one |
| Hardcoding the comparison period instead of deriving from options | Simpler calculation | Breaks when option terms change; hides normalization bugs | Never |
| Generating SVG as raw string concatenation | No template dependency | XSS vulnerabilities, unmaintainable chart code, no escaping | Never -- use a template engine or SVG library |
| Skipping input validation on numeric fields | Faster form development | Division by zero, negative term lengths, nonsensical results | Only in first prototype sprint; must be added before any user testing |
| Single monolithic calculation function | Quick to write | Untestable, each bug fix risks breaking other calculations | Only for initial proof of concept; refactor before adding second option type |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| HTMX + Python SSR | Returning full page HTML for HTMX partial requests | Check for `HX-Request` header and return only the target fragment; return full page for non-HTMX requests (progressive enhancement) |
| HTMX + Form Validation | Validating only on full form submit, not on partial updates | Return validation error HTML fragments that swap into the correct location; use appropriate HTTP status codes to trigger error display |
| SVG in HTML | Serving SVG with wrong content type or double-encoding entities | Inline SVG directly in the HTML response (no `<img>` or `<object>` tags); ensure template engine does not double-escape SVG markup |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Recalculating all options on every keystroke via HTMX | Server hammered with requests; UI feels laggy; 300ms target missed | Debounce HTMX triggers (e.g., `hx-trigger="keyup changed delay:500ms"`) or use explicit Calculate button as primary trigger | Immediately with 3-4 options and complex calculations |
| Month-by-month iteration for opportunity cost when a closed-form formula exists | Calculation takes milliseconds instead of microseconds; adds up with many options | Use compound interest formulas (future value of lump sum, future value of annuity) instead of iterating month by month | Unlikely to be a real problem at this scale, but closed-form is also simpler to verify |
| Generating large SVG charts with one `<rect>` or `<circle>` per data point per month | SVG DOM becomes heavy; browser rendering slows | For line charts, use `<polyline>` or `<path>` instead of individual elements; keep SVG element count under a few hundred | At 60+ month comparison periods with 4 options |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Injecting user input directly into SVG markup | XSS via crafted option labels (the "Custom / Other" type has a free-text label field) | Escape all user-provided text before embedding in SVG; use a template engine with auto-escaping |
| No rate limiting on calculation endpoint | DoS via automated form submissions hammering the server | Add basic rate limiting middleware (e.g., 60 requests/minute per IP); since the app is stateless, this is the main abuse vector |
| Logging form inputs for debugging and forgetting to remove | Privacy violation -- the PRD explicitly requires no user data persistence | Never log form inputs, even in debug mode; log only metadata (request timing, option count, error types) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing only the "winner" without explaining why | User does not trust the recommendation; cannot explain to spouse/partner | Always show the dollar difference AND a plain-English sentence explaining the primary driver (e.g., "because your cash earns more invested than the loan costs in interest") |
| Displaying opportunity cost as a negative number | Users think they owe money or that something went wrong | Frame opportunity cost as "investment earnings you would miss" (positive framing) or "cost of not investing" -- never show negative dollar amounts in the summary |
| Using financial jargon in labels (APR, amortization, present value) | Primary persona has no financial background; they abandon the form | Use plain language: "interest rate" not "APR" (with APR in a subtitle), "monthly payment" not "periodic installment", "what your money could earn" not "opportunity cost" |
| Not showing the monthly payment amount | Users care about monthly cash flow, not just total cost | Always display monthly payment per option even though it is not the primary metric; users need to verify affordability |
| Requiring all fields before showing any results | Users want to explore; they abandon before filling everything in | Show partial results as soon as minimum viable inputs are provided (purchase price + at least one complete option); gray out or annotate incomplete options |

## "Looks Done But Isn't" Checklist

- [ ] **Amortization math:** Final payment in schedule zeroes out remaining balance exactly (no residual cents)
- [ ] **Cash option opportunity cost:** Cash purchase shows significantly higher True Total Cost than purchase price alone (the opportunity cost should be substantial for large purchases)
- [ ] **Comparison period normalization:** Changing which option has the longest term changes the comparison period for all options
- [ ] **Deferred interest caveat:** Enabling deferred interest toggle produces a visible warning in the recommendation card
- [ ] **SVG accessibility:** Each chart has a `<title>`, `<desc>`, companion data table, and non-color-only differentiation
- [ ] **HTMX progressive enhancement:** App works fully with JavaScript disabled (form submit, full page reload, results displayed)
- [ ] **Mobile layout:** Results are reachable without excessive scrolling; sticky anchor link works
- [ ] **Edge case inputs:** 0% APR, 0 down payment, 1-month term, maximum 4 options simultaneously all produce valid results
- [ ] **Rate conversion:** Verify that $10,000 at 6% APR for 36 months produces $304.22/month (standard amortization check)
- [ ] **Inflation adjustment:** Enabling inflation actually changes the True Total Cost values (not just displayed, but correctly discounted)
- [ ] **Tax savings:** Enabling tax implications with deductible interest reduces True Total Cost for loan options but not for cash

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Float-based calculations | HIGH | Replace all `float` with `Decimal` throughout calculation engine; update all tests; verify every output |
| Wrong comparison period normalization | HIGH | Redesign cost model to include post-termination investment phase; rewrite all calculations; all test expected values change |
| Missing SVG accessibility | MEDIUM | Add ARIA attributes and companion tables to existing SVG generation; audit with screen reader |
| HTMX form state loss | MEDIUM | Restructure `hx-target` to never replace form elements; add `hx-include` directives; test all field combinations |
| Deferred interest not modeled | LOW | Add conditional warning text to recommendation template; add one calculation branch |
| Opportunity cost double-counting | MEDIUM | Audit and document the accounting model; fix affected calculations; update all test baselines |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Floating-point arithmetic | Phase 1: Calculation Engine | Unit tests comparing against known amortization tables pass to the cent |
| Comparison period normalization | Phase 1: Calculation Engine | Test: 24-month option vs 60-month option produces different True Total Cost than when both are 60-month |
| Deferred interest mismodeling | Phase 1: Calculation Engine + Phase 2: Results UI | Toggle produces visible caveat AND different cost numbers |
| Opportunity cost accounting | Phase 1: Calculation Engine | Cash purchase True Total Cost > purchase price; loan with down payment has higher opportunity cost than loan without |
| Rate conversion errors | Phase 1: Calculation Engine | Monthly payment for known scenarios matches published amortization calculators |
| SVG accessibility | Phase 2: Charts/Visualization | Axe audit passes; screen reader can describe chart content |
| HTMX form state loss | Phase 2: UI/HTMX Integration | Manual test: change option type in slot 2, verify slot 1 inputs are preserved |
| XSS via custom labels | Phase 2: UI/HTMX Integration | Input `<script>alert(1)</script>` as custom label; verify it renders as escaped text |
| No input validation | Phase 2: Form/Validation | Submit negative term, zero price, non-numeric APR; verify graceful error messages |
| Keystroke-triggered calculation spam | Phase 2: UI/HTMX Integration | Verify debounce or explicit Calculate button; check server logs under rapid typing |

## Sources

- Python `decimal` module documentation (standard library) -- well-established best practice for financial calculations
- WCAG 2.1 AA guidelines for SVG accessibility (W3C)
- HTMX documentation on `hx-target`, `hx-include`, and `hx-trigger` attributes
- Standard loan amortization formulas (corporate finance reference)
- Domain expertise on financial calculator design patterns

**Note:** Web search was unavailable during this research session. Confidence is MEDIUM rather than HIGH because findings could not be cross-referenced against current community discussions or recent post-mortems. The pitfalls documented here are well-established in the financial software and web development domains, but specific HTMX + Python SSR edge cases may exist that are not captured here.

---
*Pitfalls research for: Fathom -- Financing Options Analyzer*
*Researched: 2026-03-10*
