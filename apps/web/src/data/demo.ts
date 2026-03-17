import type {
  Assumption,
  DecisionRun,
  EvidenceFile,
  ExtractedFact,
  InterrogationTurn,
  Kpi,
  Memo,
  Project,
  RiskCell,
  RunArtifacts,
  Stakeholder,
  StakeholderEdge,
  TimelineEvent
} from "../types";

export const demoProject: Project = {
  id: "proj_demo_regional_provider",
  name: "MetroCare Reimbursement Stress Test",
  organizationName: "MetroCare Health System",
  createdAt: "2026-03-17T10:00:00.000Z",
  updatedAt: "2026-03-17T10:00:00.000Z",
  scenarioType: "reimbursement_cut"
};

export const demoRun: DecisionRun = {
  id: "run_demo_reimbursement_cut",
  projectId: demoProject.id,
  scenarioType: "reimbursement_cut",
  simulationRequirement:
    "Simulate a 7% reimbursement reduction and downstream effects on margin, staffing, patient access, and financing confidence over 30, 90, and 180 days.",
  status: "memo_ready",
  createdAt: "2026-03-17T10:05:00.000Z",
  updatedAt: "2026-03-17T10:05:00.000Z",
  timeHorizons: [30, 90, 180]
};

export const demoEvidence: EvidenceFile[] = [
  {
    id: "ev_1",
    projectId: demoProject.id,
    name: "metrocare_financials_q4.csv",
    filename: "metrocare_financials_q4.csv",
    mimeType: "text/csv",
    extension: "csv",
    size: 18420,
    sizeBytes: 18420,
    extractedPreview: "Operating margin, denial rate, and days cash on hand trends."
  },
  {
    id: "ev_2",
    projectId: demoProject.id,
    name: "state_reimbursement_bulletin.md",
    filename: "state_reimbursement_bulletin.md",
    mimeType: "text/markdown",
    extension: "md",
    size: 9111,
    sizeBytes: 9111,
    extractedPreview: "State bulletin signaling reimbursement pressure and access oversight."
  },
  {
    id: "ev_3",
    projectId: demoProject.id,
    name: "payer_denial_trend.txt",
    filename: "payer_denial_trend.txt",
    mimeType: "text/plain",
    extension: "txt",
    size: 4438,
    sizeBytes: 4438,
    extractedPreview: "Commercial payer denial trend and utilization-management tightening."
  }
];

const facts: ExtractedFact[] = [
  {
    id: "fact_1",
    evidenceFileId: "ev_1",
    factType: "financial_signal",
    title: "Margin compression is already visible",
    detail: "Operating margin fell 90 basis points quarter over quarter before the modeled reimbursement cut.",
    sourceExcerpt: "Q4 margin dropped from 4.7% to 3.8%.",
    confidence: 0.92
  },
  {
    id: "fact_2",
    evidenceFileId: "ev_3",
    factType: "payer_signal",
    title: "Denial intensity is rising",
    detail: "Denial review now adds a second medical-necessity screen on selected specialty claims.",
    sourceExcerpt: "Two-step utilization review added for orthopedics and cardiology.",
    confidence: 0.84
  },
  {
    id: "fact_3",
    evidenceFileId: "ev_2",
    factType: "regulatory_signal",
    title: "Access deterioration is likely to trigger regulator follow-up",
    detail: "State guidance ties wait-time growth to mandatory corrective action reporting.",
    sourceExcerpt: "Providers exceeding specialty access thresholds may receive remediation notices.",
    confidence: 0.78
  }
];

const assumptions: Assumption[] = [
  {
    id: "a_1",
    key: "cms_reimbursement_change",
    value: "-7%",
    statement: "CMS base reimbursement decreases by 7% effective next quarter.",
    confidence: 0.92,
    status: "confirmed",
    impactArea: "finance",
    rationale: "Grounded in the state reimbursement bulletin.",
    sourceEvidenceIds: ["ev_2"]
  },
  {
    id: "a_2",
    key: "commercial_payer_mix",
    value: "Flat for 90 days",
    statement: "Commercial payer mix remains flat during the first 90 days.",
    confidence: 0.63,
    status: "needs_review",
    impactArea: "operations",
    rationale: "Management commentary implies mix stability but with limited certainty.",
    sourceEvidenceIds: ["ev_1"]
  },
  {
    id: "a_3",
    key: "labor_overtime_cap",
    value: "Implemented by day 45",
    statement: "Labor overtime cap can be enforced by day 45 without a care-quality penalty.",
    confidence: 0.44,
    status: "missing_data",
    impactArea: "access",
    rationale: "Insufficient evidence on staffing elasticity in specialty clinics.",
    sourceEvidenceIds: ["ev_1"]
  },
  {
    id: "a_4",
    key: "lender_monitoring_threshold",
    value: "Margin below 1.5%",
    statement: "Lender covenant monitoring increases when margin drops below 1.5%.",
    confidence: 0.83,
    status: "confirmed",
    impactArea: "regulatory",
    rationale: "Historical covenant package references a margin trigger.",
    sourceEvidenceIds: ["ev_1"]
  }
];

const stakeholders: Stakeholder[] = [
  {
    id: "s_provider",
    name: "MetroCare Health System",
    type: "Provider",
    roleSummary: "System operator balancing margin preservation with care continuity.",
    incentive: "Preserve margin while protecting critical service access",
    pressurePoint: "Reimbursement compression and labor inflation",
    likelyReaction: "Freeze non-critical hiring and redesign low-margin service lines",
    influence: 96
  },
  {
    id: "s_payer",
    name: "Apex Health Plan",
    type: "Payer",
    roleSummary: "Controls claims approval cadence and realized cash flow.",
    incentive: "Control claims outflow and utilization",
    pressurePoint: "Provider renegotiation pressure",
    likelyReaction: "Increase denial scrutiny and prior-auth intensity",
    influence: 88
  },
  {
    id: "s_regulator",
    name: "State Access Office",
    type: "Regulator",
    roleSummary: "Escalates when care access deteriorates.",
    incentive: "Maintain specialty access and compliance",
    pressurePoint: "Rural clinic throughput decline",
    likelyReaction: "Issue remediation requests and reporting deadlines",
    influence: 80
  },
  {
    id: "s_lender",
    name: "Summit Regional Bank",
    type: "Lender",
    roleSummary: "Tracks liquidity burn and covenant deterioration.",
    incentive: "Protect repayment profile and monitoring rights",
    pressurePoint: "Margin drawdown and slower collections",
    likelyReaction: "Require monthly liquidity reporting and mitigation checkpoints",
    influence: 82
  },
  {
    id: "s_investor",
    name: "NorthBridge Growth Partners",
    type: "Investor",
    roleSummary: "Pushes strategic action when valuation compresses.",
    incentive: "Protect valuation and strategic optionality",
    pressurePoint: "Multi-quarter EBITDA trajectory",
    likelyReaction: "Push faster service-line rationalization and governance checkpoints",
    influence: 78
  },
  {
    id: "s_patient",
    name: "Patient Advocacy Coalition",
    type: "PatientAdvocate",
    roleSummary: "Amplifies access friction and wait-time deterioration.",
    incentive: "Avoid access erosion",
    pressurePoint: "Appointment lead-time growth",
    likelyReaction: "Escalate public and regulatory pressure around delayed specialty care",
    influence: 71
  }
];

const edges: StakeholderEdge[] = [
  {
    id: "e_1",
    source: "s_provider",
    target: "s_payer",
    relation: "CONTRACTS_WITH",
    rationale: "Revenue realization depends on payer reimbursement terms."
  },
  {
    id: "e_2",
    source: "s_regulator",
    target: "s_provider",
    relation: "REGULATES",
    rationale: "Access and compliance oversight."
  },
  {
    id: "e_3",
    source: "s_lender",
    target: "s_provider",
    relation: "FUNDS",
    rationale: "Debt facility and covenant link."
  },
  {
    id: "e_4",
    source: "s_investor",
    target: "s_provider",
    relation: "INFLUENCES",
    rationale: "Strategic capital influence."
  },
  {
    id: "e_5",
    source: "s_patient",
    target: "s_regulator",
    relation: "REPORTS_ON",
    rationale: "Access complaints drive scrutiny."
  },
  {
    id: "e_6",
    source: "s_payer",
    target: "s_patient",
    relation: "RESPONDS_TO",
    rationale: "Utilization policies affect patient experience."
  }
];

const kpis: Kpi[] = [
  {
    id: "k_margin",
    label: "Operating Margin",
    unit: "%",
    baseline: 3.8,
    byHorizon: {
      "30": {
        base_case: { projected: 2.7, delta: -1.1 },
        downside_case: { projected: 1.6, delta: -2.2 },
        severe_case: { projected: 0.3, delta: -3.5 }
      },
      "90": {
        base_case: { projected: 2.0, delta: -1.8 },
        downside_case: { projected: 0.4, delta: -3.4 },
        severe_case: { projected: -1.3, delta: -5.1 }
      },
      "180": {
        base_case: { projected: 2.6, delta: -1.2 },
        downside_case: { projected: 0.9, delta: -2.9 },
        severe_case: { projected: -1.0, delta: -4.8 }
      }
    }
  },
  {
    id: "k_denial",
    label: "Denial Rate",
    unit: "%",
    baseline: 6.1,
    byHorizon: {
      "30": {
        base_case: { projected: 7.5, delta: 1.4 },
        downside_case: { projected: 8.3, delta: 2.2 },
        severe_case: { projected: 9.5, delta: 3.4 }
      },
      "90": {
        base_case: { projected: 8.0, delta: 1.9 },
        downside_case: { projected: 9.2, delta: 3.1 },
        severe_case: { projected: 10.8, delta: 4.7 }
      },
      "180": {
        base_case: { projected: 7.4, delta: 1.3 },
        downside_case: { projected: 8.5, delta: 2.4 },
        severe_case: { projected: 9.9, delta: 3.8 }
      }
    }
  },
  {
    id: "k_access",
    label: "Specialty Wait Time",
    unit: " days",
    baseline: 21,
    byHorizon: {
      "30": {
        base_case: { projected: 23.8, delta: 2.8 },
        downside_case: { projected: 26.6, delta: 5.6 },
        severe_case: { projected: 29.2, delta: 8.2 }
      },
      "90": {
        base_case: { projected: 25.2, delta: 4.2 },
        downside_case: { projected: 28.1, delta: 7.1 },
        severe_case: { projected: 32.5, delta: 11.5 }
      },
      "180": {
        base_case: { projected: 24.1, delta: 3.1 },
        downside_case: { projected: 27.0, delta: 6.0 },
        severe_case: { projected: 30.8, delta: 9.8 }
      }
    }
  },
  {
    id: "k_liquidity",
    label: "Days Cash on Hand",
    unit: " days",
    baseline: 68,
    byHorizon: {
      "30": {
        base_case: { projected: 64.0, delta: -4.0 },
        downside_case: { projected: 60.5, delta: -7.5 },
        severe_case: { projected: 56.8, delta: -11.2 }
      },
      "90": {
        base_case: { projected: 61.2, delta: -6.8 },
        downside_case: { projected: 55.7, delta: -12.3 },
        severe_case: { projected: 49.5, delta: -18.5 }
      },
      "180": {
        base_case: { projected: 62.6, delta: -5.4 },
        downside_case: { projected: 57.2, delta: -10.8 },
        severe_case: { projected: 51.8, delta: -16.2 }
      }
    }
  }
];

const riskHeatmap: RiskCell[] = [
  {
    stakeholderId: "s_provider",
    stakeholder: "MetroCare Health System",
    operations: 88,
    finance: 94,
    access: 81,
    regulatory: 73
  },
  {
    stakeholderId: "s_payer",
    stakeholder: "Apex Health Plan",
    operations: 55,
    finance: 71,
    access: 49,
    regulatory: 63
  },
  {
    stakeholderId: "s_regulator",
    stakeholder: "State Access Office",
    operations: 62,
    finance: 40,
    access: 84,
    regulatory: 92
  },
  {
    stakeholderId: "s_lender",
    stakeholder: "Summit Regional Bank",
    operations: 34,
    finance: 86,
    access: 22,
    regulatory: 58
  },
  {
    stakeholderId: "s_investor",
    stakeholder: "NorthBridge Growth Partners",
    operations: 47,
    finance: 79,
    access: 35,
    regulatory: 51
  },
  {
    stakeholderId: "s_patient",
    stakeholder: "Patient Advocacy Coalition",
    operations: 59,
    finance: 31,
    access: 89,
    regulatory: 66
  }
];

const timeline: TimelineEvent[] = [
  {
    id: "t_1",
    day: 30,
    variant: "base_case",
    channel: "Operational Network",
    stakeholder: "MetroCare Health System",
    event: "Service-line staffing freeze starts in low-margin specialties",
    implication: "Near-term labor stabilization with moderate access friction.",
    confidence: 0.82,
    citations: ["metrocare_financials_q4.csv"]
  },
  {
    id: "t_2",
    day: 30,
    variant: "downside_case",
    channel: "External Signals",
    stakeholder: "Apex Health Plan",
    event: "Denial review policy tightens by one additional review gate",
    implication: "Cash realization delays increase working-capital stress.",
    confidence: 0.78,
    citations: ["payer_denial_trend.txt"]
  },
  {
    id: "t_3",
    day: 90,
    variant: "base_case",
    channel: "External Signals",
    stakeholder: "Summit Regional Bank",
    event: "Lender requires monthly covenant deck and mitigation tracking",
    implication: "Governance overhead rises and refinancing flexibility narrows.",
    confidence: 0.87,
    citations: ["metrocare_financials_q4.csv"]
  },
  {
    id: "t_4",
    day: 90,
    variant: "severe_case",
    channel: "Operational Network",
    stakeholder: "Patient Advocacy Coalition",
    event: "Public campaign launches over prolonged specialty wait times",
    implication: "Regulatory attention and reputational pressure accelerate.",
    confidence: 0.71,
    citations: ["state_reimbursement_bulletin.md"]
  },
  {
    id: "t_5",
    day: 180,
    variant: "base_case",
    channel: "Operational Network",
    stakeholder: "MetroCare Health System",
    event: "Service-line redesign recovers part of operating margin losses",
    implication: "Margin stabilizes but access remains fragile in two clinics.",
    confidence: 0.67,
    citations: ["metrocare_financials_q4.csv", "state_reimbursement_bulletin.md"]
  },
  {
    id: "t_6",
    day: 180,
    variant: "severe_case",
    channel: "External Signals",
    stakeholder: "NorthBridge Growth Partners",
    event: "Investor requests board-level turnaround committee escalation",
    implication: "Strategic optionality narrows and recap paths become urgent.",
    confidence: 0.74,
    citations: ["metrocare_financials_q4.csv"]
  }
];

const operatorMemo: Memo = {
  type: "operator",
  title: "Operator Brief",
  citations: ["metrocare_financials_q4.csv", "payer_denial_trend.txt", "state_reimbursement_bulletin.md"],
  sections: [
    {
      title: "Executive Summary",
      content:
        "MetroCare can absorb the first 30 days of reimbursement pressure, but by day 90 the downside case points to material margin erosion, tighter lender scrutiny, and sustained access pressure in specialty lines.",
      citations: ["metrocare_financials_q4.csv", "payer_denial_trend.txt"]
    },
    {
      title: "Scenario Assumptions",
      content:
        "The working assumption is a 7% reimbursement cut with flat commercial mix in the first 90 days and partial but uncertain labor mitigation by day 45.",
      citations: ["state_reimbursement_bulletin.md", "metrocare_financials_q4.csv"]
    },
    {
      title: "Recommended Actions",
      content:
        "Launch a denial war room, preserve cash, protect high-throughput service lines, and open lender communications before covenant pressure formalizes.",
      citations: ["metrocare_financials_q4.csv"]
    },
    {
      title: "Confidence and Blind Spots",
      content:
        "Confidence is strongest on financial exposure and weaker on labor elasticity, patient leakage, and payer response timing.",
      citations: ["state_reimbursement_bulletin.md"]
    }
  ]
};

const capitalMemo: Memo = {
  type: "capital",
  title: "Capital Memo",
  citations: ["metrocare_financials_q4.csv", "payer_denial_trend.txt"],
  sections: [
    {
      title: "Investment Committee Summary",
      content:
        "The provider remains operable in the base case, but downside and severe cases imply higher covenant monitoring, slower cash realization, and declining strategic optionality within 180 days.",
      citations: ["metrocare_financials_q4.csv"]
    },
    {
      title: "Liquidity and Covenant Implications",
      content:
        "Covenant pressure rises first through margin compression and then through slower collections and higher denial intensity. Monthly reporting should begin before the 90-day mark.",
      citations: ["metrocare_financials_q4.csv", "payer_denial_trend.txt"]
    },
    {
      title: "Capital Actions",
      content:
        "Condition any additional support on denial remediation milestones, labor stabilization, and board-level restructuring cadence.",
      citations: ["metrocare_financials_q4.csv"]
    }
  ]
};

export const demoArtifacts: RunArtifacts = {
  facts,
  assumptions,
  stakeholders,
  edges,
  kpis,
  riskHeatmap,
  timeline,
  executiveDashboard: {
    title: "MetroCare executive dashboard",
    narrative:
      "Reimbursement pressure is manageable in the first month, but downside and severe paths materially raise margin, access, and covenant risk by day 90.",
    decisionFocus:
      "Protect margin and liquidity without allowing access deterioration to trigger regulator or patient backlash.",
    metrics: [
      {
        key: "margin",
        label: "Margin Pressure",
        score: 84,
        tone: "critical",
        summary: "Reimbursement compression and denials are the lead financial threat."
      },
      {
        key: "access",
        label: "Care Access Stress",
        score: 71,
        tone: "elevated",
        summary: "Specialty wait times rise fast enough to create regulator attention."
      },
      {
        key: "capital",
        label: "Capital Confidence",
        score: 76,
        tone: "critical",
        summary: "Lender scrutiny accelerates if cash and collections do not stabilize by day 90."
      }
    ]
  },
  conflictMatrix: [
    {
      stakeholderId: "s_provider",
      stakeholder: "MetroCare Health System",
      group: "Operator",
      intensity: 88,
      concern: "Preserve margin while protecting high-risk service access.",
      likelyMove: "Freeze low-priority hiring and reprioritize service-line investment.",
      pressure: "Reimbursement compression plus labor inflation.",
      response: "Shift to denial reduction, cash preservation, and targeted operating redesign."
    },
    {
      stakeholderId: "s_lender",
      stakeholder: "Summit Regional Bank",
      group: "Capital",
      intensity: 79,
      concern: "Avoid covenant deterioration and refinancing risk.",
      likelyMove: "Increase reporting cadence and mitigation demands.",
      pressure: "Liquidity drawdown and margin compression.",
      response: "Require earlier lender communication and contingency planning."
    },
    {
      stakeholderId: "s_regulator",
      stakeholder: "State Access Office",
      group: "Regulator",
      intensity: 73,
      concern: "Avoid specialty access deterioration in vulnerable markets.",
      likelyMove: "Request remediation and monitoring updates.",
      pressure: "Wait-time growth and service-line retrenchment.",
      response: "Make access protection visible in the operating plan."
    }
  ],
  actionScenarios: [
    {
      horizonDays: 30,
      title: "Cash and Claims Stabilization",
      summary: "Use the first 30 days to stabilize claims realization and preserve liquidity.",
      operatingFocus: "Stand up a denial war room and protect critical throughput.",
      capitalFocus: "Preempt covenant anxiety with transparent lender updates.",
      boardAsk: "Approve a 30-day cash and denial-control sprint."
    },
    {
      horizonDays: 90,
      title: "Selective Service-Line Reset",
      summary: "Reallocate staffing and spend toward lines that preserve both margin and access.",
      operatingFocus: "Reshape low-margin lines without triggering public access failures.",
      capitalFocus: "Demonstrate KPI recovery and a credible mitigation cadence.",
      boardAsk: "Approve service-line redesign and tighter governance checkpoints."
    },
    {
      horizonDays: 180,
      title: "Strategic Resilience Path",
      summary: "Position the system for covenant defense, recap optionality, and a more durable operating model.",
      operatingFocus: "Preserve sustainable footprint and throughput resilience.",
      capitalFocus: "Protect flexibility for recapitalization or covenant renegotiation.",
      boardAsk: "Authorize a contingency capital and restructuring plan."
    }
  ],
  mitigationOptions: [
    {
      id: "mit_1",
      name: "Revenue Cycle Command Center",
      positioning: "Best immediate financial defense",
      composite: 84,
      marginImpact: "High positive",
      accessImpact: "Neutral to mildly positive",
      trustImpact: "Positive if denials fall quickly",
      bestUse: "First 30-day response to reimbursement and denial stress.",
      tradeoff: "Consumes leadership bandwidth and requires tight execution."
    },
    {
      id: "mit_2",
      name: "Selective Service-Line Triage",
      positioning: "Structural downside defense",
      composite: 73,
      marginImpact: "Medium to high positive",
      accessImpact: "Negative if executed too broadly",
      trustImpact: "Mixed; highly sensitive to regulator and patient optics",
      bestUse: "When downside or severe cases persist into the second quarter.",
      tradeoff: "Can create reputational and regulatory pressure without access safeguards."
    }
  ],
  memos: {
    operator: operatorMemo,
    capital: capitalMemo
  }
};

export const demoInterrogation: InterrogationTurn[] = [
  {
    question: "What is the covenant risk outlook?",
    answer:
      "Covenant risk becomes material by day 90 in the downside case unless MetroCare stabilizes denial rates, preserves cash, and starts lender communication before monthly reporting is imposed.",
    citations: ["metrocare_financials_q4.csv", "payer_denial_trend.txt"]
  },
  {
    question: "What should we decide in the next 30 days?",
    answer:
      "Prioritize denial reduction, cash preservation, and service-line triage. Those moves buy time across both operator and capital outcomes.",
    citations: ["metrocare_financials_q4.csv"]
  }
];
