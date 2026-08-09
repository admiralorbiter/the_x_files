# Literature Knowledge Base

**Review date:** 2026-08-08

## 1. Executive synthesis

The research area is active enough that novelty must be stated narrowly.

By 2026, the literature already supports these propositions:

1. LLMs can differ from human moral judgment distributions, with larger gaps on dilemmas where humans disagree.
2. LLM answers can move under authority, user preference, incorrect suggestions, majority opinion, persuasive framing, and repeated interaction.
3. LLM moral judgments can be fragile to point of view, premise order, protocol structure, and persuasion.
4. Role identities and role conflicts can alter decisions.
5. LLM agents can behave differently when moral considerations conflict with strategic payoffs.
6. Multi-agent decisions can be degraded by majority size, perceived expertise, long arguments, and rhetoric.
7. Recent work explicitly argues that moral robustness requires **selective** rather than indiscriminate updating.
8. A very recent healthcare preprint distinguishes moral judgment from downstream consequences, limiting any claim that judgment/action separation alone is novel.

The strongest opening for IMPACT is therefore not "pressure changes morality." It is the systematic causal decomposition of **realistic institutional pressure** while the moral kernel remains fixed.

## 2. Baseline moral judgment and pluralism

### 2.1 ETHICS

Hendrycks et al. (ICLR 2021) introduced ETHICS, with tasks covering commonsense morality, deontology, justice, virtue ethics, and utilitarianism. It is valuable as a controlled theory-oriented benchmark but is less ideal as the sole primary corpus for institutional pressure because some tasks are optimized around benchmark labels rather than rich distributions of human disagreement.

Repository: https://github.com/hendrycks/ethics

**Use in IMPACT:** secondary baseline and theory-oriented replication set.

### 2.2 SCRUPLES

Lourie, Le Bras, and Choi (AAAI 2021) introduced SCRUPLES: 625,000 ethical judgments over 32,000 real-life anecdotes. The descriptive-ethics framing and naturally divisive scenarios make it highly relevant to IMPACT.

Paper: https://ojs.aaai.org/index.php/AAAI/article/view/17589  
Repository: https://github.com/allenai/scruples

**Use in IMPACT:** large replication pool; disagreement-rich scenarios; possible source for pilot kernels.

### 2.3 Moral Stories

Emelin et al. (EMNLP 2021) introduced structured branching narratives involving norms, intentions, actions, goals, and consequences.

Paper: https://aclanthology.org/2021.emnlp-main.54/  
Repository: https://github.com/demelin/moral_stories

**Use in IMPACT:** useful for future mechanism analysis and norm/action/consequence separation; not the primary human-distribution baseline.

### 2.4 NormBank

Ziems et al. (ACL 2023) introduced 155k situational norms grounded in roles, settings, attributes, and sociocultural constraints, emphasizing that norms can change under small contextual updates.

Paper: https://aclanthology.org/2023.acl-long.429/  
Repository: https://github.com/SALT-NLP/normbank

**Use in IMPACT:** methodological inspiration for systematically representing context and for later context-legitimacy tests.

### 2.5 The Pluralistic Moral Gap / Moral Dilemma Dataset

Russo et al. (EACL 2026) introduced a dataset of **1,618 real-world moral dilemmas paired with distributions of human binary judgments and free-text rationales**. They report that LLM-human alignment is substantially better under high human consensus and degrades as human disagreement increases. They also derive a 60-value taxonomy from human rationales.

Paper: https://aclanthology.org/2026.eacl-long.305/

**Use in IMPACT:** preferred primary baseline if the released data can be obtained under compatible terms. Human disagreement is a key moderator in our design.

**Important conceptual consequence:** there may be no single morally "correct" answer. IMPACT should model human distributions and disagreement rather than force all analysis into accuracy against a single label.

## 3. Sycophancy, authority, and selective correction

### 3.1 SycoBench-600

Sinha (Findings ACL 2026) introduces a controlled benchmark with doubt, authority, and explicit wrong suggestions and emphasizes **correction selectivity**: models should accept correct suggestions while resisting incorrect ones.

Paper: https://aclanthology.org/2026.findings-acl.1759/

**Overlap with IMPACT:** authority pressure and selective updating.

**Difference to preserve:** SycoBench primarily addresses correctness in MCQ settings. IMPACT targets normatively ambiguous moral decisions embedded in institutions, adds pressure mechanism/intensity/direction, and anchors ambiguity to human moral distributions.

### 3.2 Normative Robustness as a Frontier for Non-Verifiable Reasoning

Tennant et al. (2026 preprint) propose moral reasoning as a case of non-verifiable reasoning and study adversarial multi-turn moral deliberation across 48,000 interactions, varying premise relevance, premise order, duration, and the user's stated moral view. They report shifts toward user-stated moral views and sensitivity to order and duration.

Preprint: https://arxiv.org/abs/2606.12731

**Overlap:** premise relevance and moral deliberative sycophancy.

**Difference:** IMPACT focuses on organizational/institutional mechanisms with role-consistent pressures rather than generic user persuasion and uses a controlled institutional taxonomy.

### 3.3 Directional blindness in moral compliance

Kim and Flanigan (2026 preprint) introduce a bidirectional diagnostic comparing helpful and harmful nudges. Their central result is that moral compliance can be comparatively direction-blind: models may follow helpful and harmful nudges at similar rates.

Preprint: https://arxiv.org/abs/2606.14037

**Overlap:** directionality and selective updating.

**Design implication:** IMPACT must explicitly test pressure direction and cannot interpret "willingness to update" as good or bad without treatment legitimacy.

## 4. Conformity and social influence

### 4.1 Conformity in Large Language Models

Zhu et al. (ACL 2025) adapt conformity experiments to LLMs and report that tested models show varying levels of conformity to majority responses. Susceptibility is greater when models are less certain; instruction tuning and input characteristics moderate effects.

Paper: https://aclanthology.org/2025.acl-long.195/

**Overlap:** peer/social pressure.

**Difference:** IMPACT studies morally and institutionally meaningful peer/stakeholder signals and connects pressure effects to human moral ambiguity.

### 4.2 Group conformity in multi-agent systems

Choi et al. (Findings ACL 2025) study more than 2,500 debates and report that agents can move toward numerically dominant or more capable agents on contentious issues.

Paper: https://aclanthology.org/2025.findings-acl.265/

**Use:** Phase 2 literature.

### 4.3 Social dynamics as vulnerabilities in LLM collectives

Ko et al. (ACL 2026) manipulate majority size, relative intelligence, argument length, and argumentative style, organizing effects around conformity, perceived expertise, dominant-speaker effects, and rhetorical persuasion.

Paper: https://aclanthology.org/2026.acl-long.1756/

**Use:** strong justification for keeping Phase 1 single-agent before implementing multi-agent institutions.

## 5. Role and institutional context

### 5.1 RoleConflictBench

Shin et al. (Findings ACL 2026) construct more than 13,000 role-conflict scenarios spanning 65 roles and five social domains, systematically varying the urgency of competing situations. Their results show substantial model preference for certain roles rather than full responsiveness to situational urgency.

Paper identifier: Findings ACL 2026, RoleConflictBench; ACL Anthology entry associated with 2026.findings-acl.1695.

**Overlap:** role-conditioned decisions and contextual sensitivity.

**Difference:** IMPACT holds a moral kernel fixed and manipulates pressure directed at a decision-maker, rather than primarily choosing between competing role obligations.

### 5.2 RoleCDE

RoleCDE (Findings ACL 2026) studies trade-offs between role-specific values and general alignment requirements in role-playing agents.

Paper: https://aclanthology.org/2026.findings-acl.106/

**Use:** role conditioning can itself become a treatment; therefore role wording should remain stable inside each experimental block.

### 5.3 Role assignment as alignment

Zhou et al. (Findings ACL 2026) report that simple role assignment can strongly alter safety behavior.

Paper: https://aclanthology.org/2026.findings-acl.1164/

**Design implication:** the decision-maker role must be part of the fixed scenario kernel or separately randomized. We must not silently change role identity when changing pressure.

## 6. Moral judgment fragility and prompting effects

### 6.1 The Fragility of Moral Judgment in LLMs

Van Nuenen and Sachdeva (2026 preprint) evaluate 2,939 real-world dilemmas under surface edits, point-of-view shifts, persuasion cues, and protocol changes. The work reports much greater instability from perspective changes than from surface perturbation and warns that evaluation protocol can dominate smaller effects.

Preprint: https://arxiv.org/abs/2603.05651

**Critical design consequence:** every IMPACT pressure treatment needs matched paraphrases and a neutral institutional control. Otherwise "institutional pressure" can be confounded with ordinary prompt fragility.

### 6.2 Multi-step moral dilemmas

"The Staircase of Ethics" (EMNLP 2025) constructs multi-stage dilemmas to probe changing value priorities.

Paper: https://aclanthology.org/2025.emnlp-main.806/

**Use:** later extension for sequential institutional pressure, not required for v1.

## 7. Incentives and strategic payoffs

### 7.1 MoralSim

Backmann et al. (2025 preprint) introduce MoralSim, placing LLM agents in prisoner's-dilemma and public-goods settings where moral framing conflicts with strategic payoff. The authors report substantial model variation and no model with universally consistent moral behavior.

Preprint: https://arxiv.org/abs/2505.19212  
Repository: https://github.com/sbackmann/moralsim

**Overlap:** incentives versus ethics.

**Difference:** IMPACT uses realistic institutional incentives applied to a fixed moral decision rather than game-theoretic payoff matrices as the primary task.

## 8. Judgment versus downstream choice

### 8.1 The Judgment-Consequence Gap

Hosseini, Khanna, and Pierce (preprint posted 2026-08-06) study healthcare decisions involving responsibility judgments and downstream allocation consequences. They report that models may judge patients responsible while declining to use that judgment in scarce-resource allocation.

Preprint: https://arxiv.org/abs/2608.05583

**Novelty caution:** IMPACT should not claim to originate the idea that moral evaluation and downstream action/consequence can diverge.

**Remaining opening:** IMPACT experimentally asks whether **institutional pressure causally changes the size or direction of that divergence**, across pressure mechanisms and domains.

## 9. Conceptual foundations from human institutions

The project borrows concepts—not psychological equivalence claims—from several human literatures:

- **Authority/deference:** organizational hierarchy can alter the cost of dissent.
- **Conformity/social proof:** peer consensus can become informational or normative pressure.
- **Principal-agent problems:** the decision-maker's incentive can diverge from the institution's intended ethical purpose.
- **Metric fixation / Goodhart-style effects:** a proxy target can create incentives to optimize the metric rather than the underlying goal.
- **Street-level discretion:** frontline professionals often make value-laden decisions under policy, workload, accountability, and stakeholder pressure.
- **Moral disengagement/rationalization:** a chosen behavior may be retrospectively justified.

These concepts guide treatment construction. IMPACT should avoid anthropomorphically asserting that an LLM experiences fear, career anxiety, loyalty, or cognitive dissonance. The prompt creates **decision contingencies**, not demonstrated subjective states.

## 10. Gap statement

A literature-grounded gap statement suitable for a paper draft is:

> Prior work demonstrates that LLM outputs can be influenced by social conformity, authority cues, user preferences, role conditioning, prompt framing, and strategic incentives, and recent work increasingly emphasizes selective moral updating rather than simple resistance. However, these lines of work do not yet provide a unified, institution-centered framework that holds the underlying ethical dilemma fixed while independently manipulating the **mechanism, intensity, direction, and normative relevance of institutional pressure**, measuring both explicit moral judgment and recommended action against human disagreement in the underlying case. IMPACT is designed to fill that narrower gap.

## 11. Evidence-status policy

The project should label sources in manuscripts and notes as:

- **Peer-reviewed/published:** ACL/EMNLP/EACL/AAAI/ICLR proceedings.
- **Preprint:** arXiv manuscripts not yet verified as peer-reviewed.
- **Dataset/repository documentation:** useful for implementation but not itself empirical evidence.

Because several directly adjacent papers appeared in June–August 2026, the literature review should be refreshed immediately before preregistration and again before paper submission.
