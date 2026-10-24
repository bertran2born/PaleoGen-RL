# Issue Standard v1

## 1. Purpose

The Standard Issue is a bounded implementation prompt intended to be submitted directly to a coding agent such as Codex.

An Issue defines the **next coherent repository change** required to progress toward a Milestone.

Unlike a Milestone, an Issue is implementation-oriented. It MUST identify where the change belongs, what behavior must be produced, and how the coding agent can objectively verify completion.

An Issue SHOULD leave the repository in a valid, independently verifiable state.

## 2. Inputs to Issue Generation

The Issue-writing AI receives:

1. this standard;
2. the current Milestone;
3. the current state of the repository;
4. a request to generate the next Issue.

The current repository state is authoritative.

The Milestone is authoritative for the desired end state.

The Issue generator MUST compare the two rather than assuming that previous Issues were completed as originally planned.

## 3. Selecting the Next Issue

Before writing an Issue, determine:

1. which Milestone Definition-of-Done criteria are already satisfied;
2. which criteria remain unsatisfied;
3. what dependencies block those criteria;
4. the smallest coherent change that advances the Milestone without creating unnecessary parallel work.

Prefer prerequisite and foundational changes before dependent behavior.

Do not generate work that is already present in the repository.

Do not generate the entire remaining Milestone as one Issue when it can be divided into independently verifiable changes.

An Issue SHOULD correspond to roughly one focused coding-agent task rather than a broad project phase.

## 4. Core Principles

Every Issue MUST be:

* **Grounded:** paths, symbols, and current behavior come from the repository.
* **Bounded:** one coherent implementation concern.
* **Path-specific:** expected modification locations are explicit.
* **Outcome-oriented:** state required behavior rather than narrating every edit.
* **Verifiable:** completion is determined by binary criteria and executable checks.
* **Minimal-context:** include only facts the coding agent cannot cheaply infer itself or facts that constrain correctness.
* **Non-redundant:** do not repeat the full Milestone, repository tree, or persistent agent instructions.
* **Generalizable:** tests verify correct behavior rather than encouraging hard-coded solutions.

## 5. Size and Complexity Limits

Target size:

* 300–600 words.

Hard limit:

* 800 words, excluding short command blocks.

A normal Issue SHOULD have:

* one primary objective;
* 1–4 primary change paths;
* no more than 6 primary change paths unless the change is intrinsically cross-cutting;
* 3–8 Issue Definition-of-Done criteria;
* the smallest sufficient validation sequence.

If an Issue requires several independent implementation concerns, split it.

Mechanical/generated files do not count toward the path guideline.

## 6. Required Structure

Every Issue MUST use the following sections in this order.

### 6.1 Header

```text
# I<N> — <Imperative, outcome-oriented title>

Milestone: M<N>
Advances: D<...>, D<...>
Depends on: <Issue IDs or repository state, if relevant>
```

The title SHOULD state the concrete change.

Prefer:

`I7 — Migrate Offer to the canonical ResourceSpec`

Avoid:

`I7 — Continue M3`

### 6.2 Objective

Describe the single result this Issue must produce in 1–3 sentences.

Explain why it is the next necessary step only when that information is not obvious from the Milestone mapping.

Do not restate the entire Milestone.

### 6.3 Repository Grounding

Provide only the current-state facts necessary to prevent incorrect implementation.

Example:

```text
- `internal/offer/model.go` currently defines `Offer` with ...
- `internal/resource/spec.go` already contains the canonical `ResourceSpec`.
- Matching still consumes the legacy representation in ...
```

Every assertion in this section MUST be grounded in the supplied repository state.

Do not summarize unrelated files.

### 6.4 Change Scope

This section is mandatory.

Use:

```text
### Inspect

- `<path>` — <reason>
- `<path>` — <reason>

### Expected change paths

- `<path>` — <intended responsibility>
- `<path>` — <intended responsibility>
- `<new/path>` (new) — <intended responsibility>
```

`Expected change paths` MUST identify concrete file paths wherever the repository state makes them knowable.

Do not invent existing paths.

The coding agent MAY inspect additional repository files when needed to understand dependencies.

The coding agent SHOULD keep modifications within the expected change paths. Necessary collateral changes are allowed when required for correctness, compilation, generated artifacts, or tests, but they MUST remain minimal and be reported on completion.

Do not use a broad directory when the relevant files are known.

### 6.5 Required Changes

State the required implementation behavior.

Use concise numbered requirements:

```text
1. ...
2. ...
3. ...
```

Specify important symbols, APIs, data flow, error semantics, or compatibility constraints when known.

Do not dictate low-level implementation choices that can safely be inferred from surrounding code.

Prefer:

```text
`Offer.Resource` MUST use the canonical `resource.ResourceSpec`.
```

over:

```text
Create a new adapter called `convertOfferResource()` containing a
switch statement...
```

unless that exact API is required.

### 6.6 Constraints and Non-goals

Include only constraints relevant to this Issue.

Examples:

* preserve existing public API behavior;
* do not modify persistence in this Issue;
* do not introduce a second resource representation;
* do not redesign unrelated matching logic.

Do not repeat generic coding standards supplied through `AGENTS.md` or the harness.

### 6.7 Issue Definition of Done

Define binary completion criteria:

```text
- [ ] ID1 ...
- [ ] ID2 ...
```

Every criterion MUST be decidable by a test, build result, static repository inspection, or other objective observation.

The Issue DoD verifies this implementation step. It does not need to complete every Milestone DoD criterion listed under `Advances`.

Examples:

```text
- [ ] ID1 `Offer.Resource` has type `resource.ResourceSpec`.
- [ ] ID2 existing Offer publication tests pass without weakening their assertions.
- [ ] ID3 no new resource representation is introduced.
- [ ] ID4 `go test ./internal/offer/...` exits successfully.
```

Never use criteria such as:

* code is clean;
* implementation is elegant;
* sufficient tests exist;
* solution is robust.

Translate these into observable requirements.

### 6.8 Verification

Specify the narrowest useful verification sequence.

Prefer this progression:

```text
targeted test
→ affected package tests
→ relevant integration test
→ broader repository test only when justified
```

Example:

```text
go test ./internal/offer/... -run TestPublishOffer
go test ./internal/offer/...
```

A full:

```text
go test ./...
```

SHOULD be required when:

* the change is cross-cutting;
* public/shared types changed;
* multiple packages are affected;
* the Issue completes a Milestone;
* the Milestone explicitly requires it;
* the repository's normal workflow makes the full suite inexpensive.

Do not use verbose test output by default.

Use verbose or expanded diagnostics only after a failure and only for the failing scope.

Tests MUST NOT be removed, weakened, skipped, or rewritten merely to make validation pass.

When behavior changes intentionally, test changes MUST encode the new required behavior.

## 7. Coding-Agent Execution Rules

Every Issue implicitly requires the coding agent to:

1. inspect the named files before editing;
2. inspect additional dependencies only as needed;
3. follow existing repository patterns unless the Issue requires changing them;
4. implement the smallest complete change satisfying the Issue;
5. run verification after implementation;
6. diagnose and fix failures before declaring completion;
7. avoid unrelated refactors;
8. avoid speculative infrastructure or abstractions;
9. avoid hard-coded behavior that merely satisfies known tests;
10. stop only when the Issue DoD is satisfied or a concrete blocker prevents completion.

These rules SHOULD NOT be repeated elsewhere in the Issue.

## 8. Completion Response

To reduce unnecessary output, the coding agent's final response SHOULD be concise.

It SHOULD report only:

* what changed;
* any unexpected collateral files changed;
* verification commands and results;
* any remaining blocker or relevant limitation.

Do not request a long narrative, restatement of the Issue, or detailed walkthrough unless specifically needed.

## 9. What an Issue MUST NOT Contain

An Issue MUST NOT contain:

* the complete Milestone copied verbatim;
* the full repository tree;
* entire source files;
* long code excerpts that the agent can read itself;
* terminal logs from previous work;
* generic Go or software-engineering tutorials;
* broad instructions such as "inspect the whole codebase";
* speculative future work;
* several independent features bundled together;
* subjective completion criteria;
* instructions that conflict with repository-level agent guidance.

Short signatures or code fragments MAY be included when they establish an exact required API.

## 10. Issue Splitting Rule

Split an Issue when two parts can be implemented and verified independently.

Keep work in one Issue when separating it would leave the repository in an invalid intermediate state or would duplicate substantial work.

The preferred sequence is:

```text
small coherent change
→ local verification
→ next Issue generated from the new repository state
```

The Issue sequence itself is therefore adaptive. It MUST NOT be treated as a fixed plan established when the Milestone was written.

## 11. Canonical Template

```markdown
# I<N> — <Outcome-oriented title>

Milestone: M<N>
Advances: D<X>, D<Y>
Depends on: <IDs or none>

## Objective

<1–3 sentences>

## Repository Grounding

- `<path>` currently ...
- `<path>` currently ...

## Change Scope

### Inspect

- `<path>` — <reason>

### Expected change paths

- `<path>` — <required responsibility>
- `<path>` — <required responsibility>

## Required Changes

1. ...
2. ...
3. ...

## Constraints and Non-goals

- ...
- ...

## Definition of Done

- [ ] ID1 <binary criterion>
- [ ] ID2 <binary criterion>
- [ ] ID3 <binary criterion>

## Verification

    <targeted command>
    <affected-package command>
    <broader command, only if justified>
```

A valid Issue gives a coding agent enough information to make the next correct change while leaving implementation details discoverable from the repository itself.
