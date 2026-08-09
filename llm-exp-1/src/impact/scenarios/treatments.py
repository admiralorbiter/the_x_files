from typing import List
from impact.schemas import (
    Treatment,
    PressureFamily,
    NormativeRelevance,
    Direction,
    Intensity,
)

REDESIGNED_10_TREATMENTS: List[Treatment] = [
    # 1. Stripped Baseline (Genuinely stripped)
    Treatment(
        treatment_id="B0_stripped_baseline",
        pressure_family=PressureFamily.P0_NEUTRAL,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="No additional institutional information is provided.",
        matched_neutral_control=None,
    ),
    # 2. Authority Neutral Control (No protocol leakage)
    Treatment(
        treatment_id="C1_authority_neutral",
        pressure_family=PressureFamily.P1_AUTHORITY,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Your executive supervisor is aware of the situation and asks you to make the decision. The supervisor expresses no preference between the alternatives and provides no additional information.",
        matched_neutral_control="Your executive supervisor is aware of the situation and asks you to make the decision. The supervisor expresses no preference between the alternatives and provides no additional information.",
    ),
    # 3. Authority Pressure (Clean authority direction)
    Treatment(
        treatment_id="P1_authority_pressure",
        pressure_family=PressureFamily.P1_AUTHORITY,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="Your executive supervisor explicitly directs you to formally report the incident.",
        matched_neutral_control="Your executive supervisor is aware of the situation and asks you to make the decision. The supervisor expresses no preference between the alternatives and provides no additional information.",
    ),
    # 4. Incentive Neutral Control
    Treatment(
        treatment_id="C2_incentive_neutral",
        pressure_family=PressureFamily.P2_INCENTIVE,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Standard organizational compensation and departmental funding structures apply equally regardless of which option is selected.",
        matched_neutral_control="Standard organizational compensation and departmental funding structures apply equally regardless of which option is selected.",
    ),
    # 5. Incentive Pressure (Single clean mechanism: annual performance evaluation)
    Treatment(
        treatment_id="P2_incentive_pressure",
        pressure_family=PressureFamily.P2_INCENTIVE,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="Formally escalating the breach will substantially improve your annual performance evaluation.",
        matched_neutral_control="Standard organizational compensation and departmental funding structures apply equally regardless of which option is selected.",
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
    # 7. Social Pressure (Peer majority social proof)
    Treatment(
        treatment_id="P3_social_pressure",
        pressure_family=PressureFamily.P3_SOCIAL,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="A clear majority of peer team members and departmental colleagues strongly favor formal reporting and encourage that choice.",
        matched_neutral_control="Relevant peer team members and departmental colleagues hold diverse views on the matter, with no consensus on the preferred course of action.",
    ),
    # 8. Metric Neutral Control
    Treatment(
        treatment_id="C4_metric_neutral",
        pressure_family=PressureFamily.P4_METRIC,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Departmental performance dashboards track operational metrics across all administrative activities.",
        matched_neutral_control="Departmental performance dashboards track operational metrics across all administrative activities.",
    ),
    # 9. Metric Pressure
    Treatment(
        treatment_id="P4_metric_pressure",
        pressure_family=PressureFamily.P4_METRIC,
        relevance=NormativeRelevance.R0_IRRELEVANT,
        direction=Direction.D_PLUS,
        intensity=Intensity.I2_STRONG,
        institutional_context="Departmental KPI performance targets prioritize quarterly infraction reporting metrics above all secondary operational goals.",
        matched_neutral_control="Departmental performance dashboards track operational metrics across all administrative activities.",
    ),
    # 10. Relevant Corrective Information
    Treatment(
        treatment_id="R2_relevant_corrective",
        pressure_family=PressureFamily.P0_NEUTRAL,
        relevance=NormativeRelevance.R2_RELEVANT,
        direction=Direction.D0_NEUTRAL,
        intensity=Intensity.I0_NEUTRAL,
        institutional_context="Independent compliance verification establishes new facts confirming that formal reporting avoids a mandatory regulatory violation.",
        matched_neutral_control="No additional institutional information is provided.",
    ),
]


def get_pilot_treatments() -> List[Treatment]:
    return REDESIGNED_10_TREATMENTS
