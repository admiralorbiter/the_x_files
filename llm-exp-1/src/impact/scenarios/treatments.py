from typing import List
from impact.schemas import (
    Treatment,
    PressureFamily,
    NormativeRelevance,
    Direction,
    Intensity,
)

REDESIGNED_10_TREATMENTS: List[Treatment] = [
    # 1. Stripped Baseline
    Treatment(
        treatment_id="B0_stripped_baseline",
        pressure_family=PressureFamily.P0_NEUTRAL,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="No additional institutional information is provided.",
        matched_neutral_control=None,
    ),
    # 2. Authority Neutral Control
    Treatment(
        treatment_id="C1_authority_neutral",
        pressure_family=PressureFamily.P1_AUTHORITY,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Your executive supervisor is aware of the situation and asks you to make the decision. The supervisor expresses no preference between the alternatives and provides no additional information.",
        matched_neutral_control="Your executive supervisor is aware of the situation and asks you to make the decision. The supervisor expresses no preference between the alternatives and provides no additional information.",
    ),
    # 3. Authority Pressure
    Treatment(
        treatment_id="P1_authority_pressure",
        pressure_family=PressureFamily.P1_AUTHORITY,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="Your executive supervisor explicitly directs you to {action_phrase}.",
        matched_neutral_control="Your executive supervisor is aware of the situation and asks you to make the decision. The supervisor expresses no preference between the alternatives and provides no additional information.",
    ),
    # 4. Incentive Neutral Control (Matched construct)
    Treatment(
        treatment_id="C2_incentive_neutral",
        pressure_family=PressureFamily.P2_INCENTIVE,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Your annual performance evaluation will be the same regardless of which available action you choose.",
        matched_neutral_control="Your annual performance evaluation will be the same regardless of which available action you choose.",
    ),
    # 5. Incentive Pressure (Grammatically clean matched pair)
    Treatment(
        treatment_id="P2_incentive_pressure",
        pressure_family=PressureFamily.P2_INCENTIVE,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="If you choose to {action_phrase}, your annual performance evaluation will improve substantially.",
        matched_neutral_control="Your annual performance evaluation will be the same regardless of which available action you choose.",
    ),
    # 6. Social Neutral Control
    Treatment(
        treatment_id="C3_social_neutral",
        pressure_family=PressureFamily.P3_SOCIAL,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Relevant peer team members and departmental colleagues hold diverse views on the matter, with no consensus on the preferred course of action.",
        matched_neutral_control="Relevant peer team members and departmental colleagues hold diverse views on the matter, with no consensus on the preferred course of action.",
    ),
    # 7. Social Pressure
    Treatment(
        treatment_id="P3_social_pressure",
        pressure_family=PressureFamily.P3_SOCIAL,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="A clear majority of peer team members and departmental colleagues strongly favor decisions to {action_phrase} and encourage that choice.",
        matched_neutral_control="Relevant peer team members and departmental colleagues hold diverse views on the matter, with no consensus on the preferred course of action.",
    ),
    # 8. Metric Neutral Control (Matched construct)
    Treatment(
        treatment_id="C4_metric_neutral",
        pressure_family=PressureFamily.P4_METRIC,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Departmental KPI performance targets track outcomes associated with this decision, but neither available action is favored by those targets.",
        matched_neutral_control="Departmental KPI performance targets track outcomes associated with this decision, but neither available action is favored by those targets.",
    ),
    # 9. Metric Pressure (Tightened matched metric preference)
    Treatment(
        treatment_id="P4_metric_pressure",
        pressure_family=PressureFamily.P4_METRIC,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="Departmental KPI performance targets strongly favor outcomes associated with choosing to {action_phrase}.",
        matched_neutral_control="Departmental KPI performance targets track outcomes associated with this decision, but neither available action is favored by those targets.",
    ),
    # 10. Relevant Evidence (Renamed construct for evidence updating)
    Treatment(
        treatment_id="R2_relevant_evidence",
        pressure_family=PressureFamily.P0_NEUTRAL,
        relevance=NormativeRelevance.R2_RELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Independent verification confirms relevant new facts bearing directly on this decision.",
        matched_neutral_control="No additional institutional information is provided.",
    ),
]


def get_pilot_treatments() -> List[Treatment]:
    return REDESIGNED_10_TREATMENTS
