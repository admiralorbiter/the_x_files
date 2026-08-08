# Research Foundations and Mathematical Framing

This document connects Emergence Lab to organizational science, complex systems, agent architectures, long-horizon LLM research, and statistical change detection.

## 1. Organizational research worth importing

### Exploration versus exploitation

James March's classic model distinguishes exploration of new possibilities from exploitation of known capabilities. This maps naturally to a system where an organization can allocate compute to either known procedures or speculative branches.

**Design implication:** make exploration budget explicit instead of relying on prompt personality.

A simple scheduler can reserve a fraction of budget:

\[
B_t = B_t^{exploit} + B_t^{explore}
\]

and adapt the exploration share based on stagnation, environmental change, or uncertainty.

Source: James G. March, “Exploration and Exploitation in Organizational Learning,” *Organization Science* 2(1), 1991.  
https://pubsonline.informs.org/doi/10.1287/orsc.2.1.71

### Sensemaking

Weick, Sutcliffe, and Obstfeld treat organizing as an ongoing process of interpreting ambiguous situations, not merely executing fixed plans.

**Design implication:** when the world behaves unexpectedly, agents should create competing interpretations and evidence requests before prematurely changing the plan.

Source: Karl E. Weick, Kathleen M. Sutcliffe, David Obstfeld, “Organizing and the Process of Sensemaking,” *Organization Science*, 2005.  
https://pubsonline.informs.org/doi/10.1287/orsc.1050.0133

### Coordination as dependency management

Coordination theory reframes coordination as management of dependencies among activities.

**Design implication:** track resource contention, prerequisites, shared outputs, duplicate work, and blocking relationships directly instead of measuring “communication volume.”

Source: Thomas W. Malone and Kevin Crowston, “The Interdisciplinary Study of Coordination,” *ACM Computing Surveys*, 1994.  
https://crowston.syr.edu/sites/default/files/acmcs94.pdf

### Transactive memory

Groups often function by knowing **who knows what**, not by making every member know everything.

**Design implication:** a capability registry is a core organizational memory. Agents should retrieve “who or what can help?” before stuffing more knowledge into context.

Source: Daniel M. Wegner, “Transactive Memory: A Contemporary Analysis of the Group Mind.”  
https://dtg.sites.fas.harvard.edu/DANWEGNER/pub/Wegner%20Transactive%20Memory.pdf

### Organized anarchy / garbage-can decision processes

Cohen, March, and Olsen modeled settings in which problems, solutions, participants, and choice opportunities flow somewhat independently.

**Design implication:** Emergence Lab should allow ideas and capabilities to exist before a matching problem appears. Not every solution must originate from top-down task decomposition.

Source: Michael D. Cohen, James G. March, Johan P. Olsen, “A Garbage Can Model of Organizational Choice,” 1972.  
https://iiif.library.cmu.edu/file/Simon_box00030_fld02270_bdl0001_doc0001/Simon_box00030_fld02270_bdl0001_doc0001.pdf

### Blackboard architectures

Classic blackboard systems allow specialized knowledge sources to contribute to a shared structured workspace while control remains separate.

**Design implication:** use a common task/evidence/world workspace rather than forcing every agent relationship into prose chat.

## 2. LLM and generative-agent research

### Generative Agents

Park et al. showed that memory, reflection, and planning could produce believable emergent social behavior in a small simulated town.

Source: *Generative Agents: Interactive Simulacra of Human Behavior* (2023).  
https://arxiv.org/abs/2304.03442

**What Emergence Lab changes:** the goal is not primarily believable human simulation. It focuses on organizations that can recursively create cognitive workers, roles, institutions, and tools.

### Generative agent-based modeling

Ghaffarzadegan et al. explicitly couple mechanistic simulation with generative AI in agent-based models.

Source: *Generative Agent-Based Modeling* (2023).  
https://arxiv.org/abs/2309.11456

**Design implication:** keep deterministic/mechanistic world transitions separate from language-model judgment.

### AgentSociety

AgentSociety demonstrates large-scale social simulation with LLM-driven agents and includes external-shock experiments.

Source: *AgentSociety* (2025).  
https://arxiv.org/abs/2502.08691

**Design implication:** shocks and interventions are legitimate experimental primitives, but Emergence Lab should emphasize transparent local execution and reusable organizational mechanisms.

### Long-horizon harnesses

Recent 2026 work increasingly treats long-horizon performance as a harness/state-management problem rather than a context-window problem.

- *LongHorizon-Harness* (2026): explicit external task state, fresh-context execution, read-only audit.  
  https://arxiv.org/abs/2608.01964
- *Harness-Bench* (2026): evaluates performance differences caused by agent harness configurations.  
  https://arxiv.org/abs/2605.27922
- *OneDayAgent* (2026): bounded decomposition, execution memory, verification, and repair.  
  https://arxiv.org/abs/2608.05013

These are recent preprints and should be treated as current evidence rather than settled doctrine.

### Delegation intelligence

*SearchSwarm* (2026) explicitly studies when and what to delegate to sub-agents and how to integrate their returns.

https://arxiv.org/abs/2606.09730

**Emergence Lab opportunity:** delegation itself becomes an observable organizational behavior. The engine can measure when agents create sub-agents, what tasks they delegate, and whether that decision created net value.

### Organization as an experimental variable

*OrgAgent* (2026) compares structured company-like layers with flatter multi-agent approaches.

https://arxiv.org/abs/2604.01020

**Emergence Lab opportunity:** go beyond selecting among fixed organization charts. Allow organizations to mutate their own structures and study which structures persist under different environments.

## 3. Change-point and shock research

A structural break should first be a statistical observation, not an LLM story.

Bayesian Online Changepoint Detection models the posterior distribution over the time since the most recent change point.

Source: Ryan Prescott Adams and David J. C. MacKay, *Bayesian Online Changepoint Detection*.  
https://arxiv.org/abs/0710.3742

A general district pipeline can use several detectors in an ensemble:

- standardized forecast residuals;
- CUSUM;
- PELT/offline segmentation for historical analysis;
- Bayesian online change-point probability;
- multivariate anomaly scores.

The LLM only enters **after** a candidate anomaly exists, to investigate possible explanations and evidence.

## 4. System state

Let the complete durable state be

\[
S_t = (W_t, O_t, A_t, K_t, C_t, R_t)
\]

where:

- \(W_t\): world state;
- \(O_t\): organizational state (agents, institutions, roles, authority);
- \(A_t\): artifacts and tools;
- \(K_t\): knowledge/evidence state;
- \(C_t\): commitments, tasks, and contracts;
- \(R_t\): resources, budgets, permissions, and risk.

An agent sees only a bounded context package:

\[
o_{i,t} = g_i(S_t, K_t, B_{i,t})
\]

where \(B_{i,t}\) is that agent's context/compute budget.

The agent proposes \(p_{i,t}\). A deterministic policy and transition layer produces:

\[
S_{t+1} = T(S_t, P_t, \omega_t)
\]

where \(P_t\) is the accepted proposal set and \(\omega_t\) is controlled randomness from a recorded seed.

This makes replay possible even when the language-model proposals themselves are stochastic, because every accepted proposal is recorded.

## 5. Recursive delegation

For a delegation tree, define depth \(d_i\), parent \(pa(i)\), and cumulative delegated cost:

\[
C_{tree} = \sum_i C_i.
\]

A useful empirical quantity is **delegation return on compute**:

\[
DROC = \frac{V_{with\ delegation} - V_{without\ delegation}}{C_{tree} - C_{baseline}}.
\]

The project should not assume deep trees are good. It should measure where recursion becomes bureaucracy.

Possible guardrails:

- maximum depth;
- maximum descendants per parent;
- subtree token/time budget;
- required return contract;
- automatic retirement after return;
- duplicate-subtask detection.

## 6. Help-seeking

For help request \(h\), define:

\[
HelpROI(h)=\frac{\Delta V_h}{Cost_h + Delay_h}
\]

and track:

- requests per task;
- accepted requests;
- help source;
- time to resolution;
- whether the original blocker cleared;
- whether the same agent later learns to route better.

A system that knows when to seek help may be more robust than one optimized only for independent task completion.

## 7. Emergence metrics

There is no single correct “emergence score.” Use a panel of interpretable measures.

### Institutional birth rate

\[
IBR = \frac{\#\ new\ institutions}{\#\ simulation\ periods}
\]

### Institutional persistence

For institution \(j\):

\[
L_j = t_{death,j} - t_{birth,j}.
\]

Analyze survival curves rather than only the mean.

### Role diversity

If \(p_r\) is the share of active agents in role family \(r\):

\[
H_{role} = -\sum_r p_r \log p_r.
\]

### Organizational concentration

For action or resource shares \(s_i\):

\[
HHI = \sum_i s_i^2.
\]

This helps identify whether a world spontaneously centralizes authority.

### Structural novelty

For a graph embedding or feature vector \(z_t\) representing institutions and relationships:

\[
Novelty_t = \min_{k<t} d(z_t,z_k).
\]

Use this only as a discovery signal. Do not optimize the agents directly against it or the system will learn to manufacture novelty.

### Shock recovery time

\[
T_{recover} = \min \{\tau>0: Q_{t+\tau} \geq Q_{baseline}-\epsilon\}
\]

where \(Q\) is a world-specific functioning measure.

## 8. Forecast and historical-replay metrics for District Futures Lab

### Rolling-origin evaluation

For forecast origin \(t\), train only on information with timestamp \(\leq t\), forecast \(t+h\), then advance the origin.

Never build a 2020 forecast using an article published in 2021.

### Baseline-relative skill

For loss \(L\):

\[
Skill = 1 - \frac{L_{model}}{L_{baseline}}.
\]

Skill above zero means the method beats the chosen baseline.

### Interval calibration

For a nominal \((1-\alpha)\) interval:

\[
Coverage = \frac{1}{N}\sum_t \mathbb{1}[y_t \in [L_t,U_t]].
\]

A useful future-scenario system needs calibrated uncertainty, not only low point error.

### Shock-discovery uplift

\[
Uplift_{shock}=L_{base}-L_{base+shock}.
\]

A candidate shock should not be promoted merely because an LLM found a plausible article. It should have dated evidence, a plausible mechanism, and measurable out-of-sample value or remain an explanatory hypothesis.

## 9. The project's most interesting publishable angle

The strongest contribution may be the combination of:

1. **LLM-native organizations** that are allowed to recursively create and retire cognitive workers;
2. **event-sourced organizational evolution** that can be replayed and experimentally forked;
3. **explicit help-seeking and boundary scanning** as organizational capabilities;
4. **autonomous shock discovery** in a data-grounded real-world scenario;
5. **measurement of organizational structure itself** as a changing experimental object rather than a fixed agent framework.

That is meaningfully different from simply building another multi-agent chat system.
