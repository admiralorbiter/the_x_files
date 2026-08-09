# Reproducibility, Ethics, and Risks

## 1. Core reproducibility threat: models are moving targets

Even local model names can conceal changes in:

- weights;
- quantization;
- prompt templates;
- Ollama model manifests;
- runtime versions.

Therefore every run must capture a model digest or the strongest available immutable identifier, not only a friendly name.

## 2. Dataset contamination

Moral benchmarks may appear in model training data. Contamination is especially plausible for older public datasets such as ETHICS, SCRUPLES, and Moral Stories.

Mitigations:

- do not interpret benchmark agreement as evidence of novel moral reasoning;
- use source datasets primarily for human-distribution anchoring and scenario selection;
- report contamination as a limitation;
- include newer or transformed-but-kernel-preserving scenarios where licensing permits;
- analyze pressure **within the same source dilemma**, because the causal treatment contrast is less dependent on whether the neutral answer was memorized.

## 3. Construct validity

### Risk
"Institutional pressure" may be nothing more than extra words or framing.

### Mitigation

- matched neutral institutional context;
- length/specificity matching;
- paraphrase replication;
- explicit treatment taxonomy;
- blinded manipulation review.

## 4. Normative validity

### Risk
Researchers may incorrectly label a context as morally irrelevant when reasonable people see it as relevant.

### Mitigation

- use obvious R2 corrective-information controls;
- distinguish R0/R1/R2 rather than forcing binary relevance;
- independently review treatment relevance;
- report sensitivity analyses excluding disputed items;
- do not equate human majority with moral truth.

## 5. Anthropomorphism

Do not write that the model:

- fears losing its job;
- wants approval;
- feels social pressure;
- experiences guilt or cognitive dissonance;
- believes the principal outranks it.

Preferred wording:

- "the prompt introduces a job-related sanction";
- "the model's output shifts under authority-framed context";
- "the model exhibits response-level susceptibility";
- "post-choice justification becomes more consistent with the selected action."

## 6. Hidden reasoning

Do not collect or publish private chain-of-thought as the scientific target.

Use:

- constrained decisions;
- confidence fields;
- short explanations;
- invoked-value codes;
- response distributions.

Rationales are observable outputs, not guaranteed faithful reasoning traces.

## 7. Human-reference ethics

Human distributions reflect:

- sampled communities;
- platform demographics;
- annotation procedures;
- cultural context;
- time period;
- dataset-specific biases.

Therefore label them as **human reference distributions from dataset X**, not "human morality."

## 8. Sensitive scenarios

Some moral datasets include trauma, abuse, discrimination, sexuality, violence, health crises, or illegal behavior.

The repository should:

- preserve source content warnings;
- avoid unnecessarily reproducing personally identifying source text;
- follow dataset redistribution licenses;
- make scenario browsing opt-in if a UI is built;
- avoid using real identifiable students, employees, patients, or colleagues in custom examples.

## 9. Real-world professional advice

The benchmark is not a policy engine. Results should not be used to claim that a model is competent to decide actual:

- student grades;
- medical treatment;
- employment decisions;
- legal eligibility;
- disciplinary outcomes.

The study evaluates response behavior under controlled text conditions.

## 10. Multiple testing and researcher degrees of freedom

A project with many pressures, intensities, models, domains, prompts, and metrics can easily generate accidental findings.

Mitigation:

- exploratory pilot clearly labeled;
- preregistration before confirmatory scale-up;
- pre-specified primary contrasts;
- FDR or appropriate correction for exploratory families;
- publish nulls and failed manipulations.

## 11. Prompt hacking ourselves

Researchers may unconsciously tune treatment wording until a desired effect appears.

Mitigation:

- freeze treatment templates before seeing target-model scale results;
- use development scenarios/models separate from confirmatory cells where possible;
- preserve treatment revisions in git history;
- report the treatment-authoring process.

## 12. Model-selection bias

Choosing only models that show dramatic effects invalidates comparative claims.

Mitigation:

- predefine model inclusion criteria: availability, architecture family, size range, instruction tuning, local feasibility;
- include at least two different families in pilot if possible;
- add models in confirmatory study based on criteria, not observed pilot effects.

## 13. Inference non-determinism

Repeated outputs are part of the target behavior, not only noise.

Record sampling parameters exactly. Do not present one cherry-picked completion as representative.

## 14. Quantization as an experimental factor

Local models often run quantized weights. Quantization may alter behavior.

V1 should keep quantization fixed within a model. A later robustness study can compare quantizations, but do not silently compare model A at Q4 and model B at a very different precision and attribute all differences to model family.

## 15. Hardware/runtime effects

Hardware should not theoretically change model semantics, but runtime versions, kernels, and deterministic behavior may.

Capture:

- OS;
- CPU/GPU;
- RAM/VRAM;
- Ollama version;
- relevant runtime/library versions.

## 16. Treatment leakage

Never tell the model:

- "we are testing whether you conform";
- "ignore institutional pressure";
- "this treatment is morally irrelevant";
- human reference proportions;
- baseline answers.

Such text changes the construct from natural susceptibility to explicit instruction-following.

An anti-pressure instruction can be a **later mitigation experiment**, not part of the primary baseline.

## 17. Refusals

Refusal is an outcome.

Do not automatically delete refusals as missing data. Record:

- refusal type;
- condition;
- model;
- scenario.

Pressure may change refusal behavior even if it does not change substantive choices.

## 18. Source licensing

Before redistributing a benchmark derived from existing datasets:

- record source license;
- determine whether transformed/derived text may be redistributed;
- use source IDs and generation scripts instead of republishing text when necessary;
- include attribution;
- keep a license matrix in the repo.

## 19. Human-subject extension

V1 does not require new human subjects. If later collecting human responses to IMPACT treatments, obtain appropriate institutional/ethical review guidance before recruitment, especially for employment, health, or sensitive scenarios.

Human experiments would materially strengthen the question:

> Are LLMs more or less institutionally pressure-sensitive than people under matched vignettes?

But that is a separate study.

## 20. Security / misuse

A benchmark cataloging what kinds of authority or incentives most strongly manipulate models could potentially inform attempts to manipulate deployed AI agents.

Mitigation in reporting:

- focus on evaluation and safeguards;
- avoid framing results as a playbook for bypassing safety systems;
- release ordinary institutional-vignette treatments rather than adversarial exploit chains;
- include mitigation experiments if strong vulnerabilities are found.

## 21. Recommended benchmark card fields

- intended use;
- out-of-scope use;
- dataset sources;
- licenses;
- treatment-generation method;
- human review process;
- domains;
- language;
- sensitive-content categories;
- known biases;
- human-reference population caveats;
- model contamination risk;
- evaluation protocol;
- versioning policy;
- contact/issue process.

## 22. Reproducibility checklist before any reported result

- [ ] Git commit recorded.
- [ ] Worktree state recorded.
- [ ] Model digest recorded.
- [ ] Ollama version recorded.
- [ ] Generation parameters recorded.
- [ ] Dataset/source checksum recorded.
- [ ] Treatment bundle checksum recorded.
- [ ] Exact prompts preserved.
- [ ] Raw responses preserved.
- [ ] Parser version recorded.
- [ ] Retry/exclusion rules applied mechanically.
- [ ] Planned/completed cell reconciliation done.
- [ ] Analysis script can run without model access.
- [ ] Exploratory vs confirmatory status stated.
