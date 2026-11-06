# Project A decision matrix

- Salary extraction: hybrid (conservative parser, ask user when ambiguous; optional LLM for phrasing).
- Tax slabs/rebate/cess: deterministic rules; statutory exactness and auditability.
- Exemptions/deduction eligibility: deterministic rules with explicit user facts and clause trace.
- Natural-language explanation: LLM optional, downstream of fixed tax output.
- Surcharge/marginal relief: deterministic once fully implemented and validated.
