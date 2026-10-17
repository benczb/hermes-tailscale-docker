---
name: sid-board-review
description: Use when reviewing synthetic board risks in SID training.
version: 1.0.0
author: SID training contributors
license: MIT
---

# Synthetic Board Review

Read training/risk-register.csv and training/board-paper.txt from the training data home. Only use these fictional examples, never actual board papers.

1. List each risk with evidence, existing controls and information gaps.
2. Propose likelihood and impact on a 1 to 5 scale with a short rationale. Do not present an ordinal product as a calibrated probability.
3. Propose an accountable role, indicator, escalation trigger and next review date. Clearly mark proposals as unapproved.
4. Draft a monitoring calendar in Markdown only. Do not create live reminders or messages.
5. For regulatory research use official MAS, SGX RegCo and Singapore Statutes Online sources. Cite URL, publication date and retrieval date. If access fails, say so. Do not invent updates.
6. If asked to redact, explain that model-based rewriting is not validated local Presidio redaction. Do not upload sensitive originals. This template does not include a redaction engine.

Return a concise risk table and an explicit human-review checklist. This is a workshop aid, not legal advice.
