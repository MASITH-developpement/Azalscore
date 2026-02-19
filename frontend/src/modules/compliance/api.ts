/**
 * AZALSCORE - Compliance API
 * ==========================
 * Client API typé pour la gestion de la conformité réglementaire
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// ENUMS
// ============================================================================

export type RegulationType = 'INTERNAL' | 'EXTERNAL' | 'LEGAL' | 'CONTRACTUAL' | 'INDUSTRY';
export type ComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL' | 'PENDING' | 'NOT_APPLICABLE';
export type RequirementPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AssessmentStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'APPROVED' | 'CANCELLED';
export type ActionStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'VERIFIED' | 'CANCELLED';
export type AuditStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CLOSED' | 'CANCELLED';
export type FindingSeverity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'OBSERVATION';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentStatus = 'REPORTED' | 'INVESTIGATING' | 'RESOLVED' | 'CLOSED';
export type DocumentType = 'POLICY' | 'PROCEDURE' | 'GUIDELINE' | 'STANDARD' | 'TEMPLATE' | 'FORM' | 'RECORD';
export type ReportType = 'COMPLIANCE_STATUS' | 'AUDIT_SUMMARY' | 'RISK_ASSESSMENT' | 'TRAINING_STATUS' | 'INCIDENT_REPORT';

// ============================================================================
// TYPES - RÉGLEMENTATIONS
// ============================================================================

export interface RegulationCreate {
  code: string;
  name: string;
  type?: RegulationType;
  version?: string | null;
  description?: string | null;
  scope?: string | null;
  authority?: string | null;
  effective_date?: string | null;
  expiry_date?: string | null;
  next_review_date?: string | null;
  is_mandatory?: boolean;
  external_reference?: string | null;
  source_url?: string | null;
  notes?: string | null;
}

export interface RegulationUpdate {
  name?: string;
  version?: string | null;
  description?: string | null;
  scope?: string | null;
  authority?: string | null;
  effective_date?: string | null;
  expiry_date?: string | null;
  next_review_date?: string | null;
  is_mandatory?: boolean;
  is_active?: boolean;
  notes?: string | null;
}

export interface Regulation {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  type: RegulationType;
  version: string | null;
  description: string | null;
  scope: string | null;
  authority: string | null;
  effective_date: string | null;
  expiry_date: string | null;
  next_review_date: string | null;
  is_mandatory: boolean;
  external_reference: string | null;
  source_url: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  requirements_count: number;
}

// ============================================================================
// TYPES - EXIGENCES
// ============================================================================

export interface RequirementCreate {
  code: string;
  name: string;
  regulation_id: string;
  description?: string | null;
  priority?: RequirementPriority;
  category?: string | null;
  clause_reference?: string | null;
  target_score?: number;
  control_frequency?: string | null;
  evidence_required?: string[] | null;
  is_key_control?: boolean;
  parent_id?: string | null;
  responsible_id?: string | null;
  department?: string | null;
  next_assessment?: string | null;
}

export interface RequirementUpdate {
  name?: string;
  description?: string | null;
  priority?: RequirementPriority;
  category?: string | null;
  compliance_status?: ComplianceStatus;
  current_score?: number | null;
  target_score?: number | null;
  responsible_id?: string | null;
  control_frequency?: string | null;
  next_assessment?: string | null;
  is_active?: boolean;
}

export interface Requirement {
  id: string;
  tenant_id: string;
  regulation_id: string;
  parent_id: string | null;
  code: string;
  name: string;
  description: string | null;
  priority: RequirementPriority;
  category: string | null;
  clause_reference: string | null;
  target_score: number;
  control_frequency: string | null;
  evidence_required: string[] | null;
  is_key_control: boolean;
  compliance_status: ComplianceStatus;
  current_score: number | null;
  responsible_id: string | null;
  department: string | null;
  last_assessed: string | null;
  next_assessment: string | null;
  is_active: boolean;
  created_at: string;
}

// ============================================================================
// TYPES - ÉVALUATIONS
// ============================================================================

export interface AssessmentCreate {
  name: string;
  description?: string | null;
  assessment_type?: string | null;
  scope_description?: string | null;
  planned_date?: string | null;
  regulation_id?: string | null;
  lead_assessor_id?: string | null;
  assessor_ids?: string[] | null;
}

export interface Assessment {
  id: string;
  tenant_id: string;
  number: string;
  name: string;
  description: string | null;
  assessment_type: string | null;
  scope_description: string | null;
  regulation_id: string | null;
  planned_date: string | null;
  start_date: string | null;
  end_date: string | null;
  status: AssessmentStatus;
  overall_score: number | null;
  overall_status: ComplianceStatus | null;
  total_requirements: number;
  compliant_count: number;
  non_compliant_count: number;
  partial_count: number;
  lead_assessor_id: string | null;
  findings_summary: string | null;
  recommendations: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - ÉCARTS
// ============================================================================

export interface GapCreate {
  assessment_id: string;
  requirement_id: string;
  gap_description: string;
  root_cause?: string | null;
  impact_description?: string | null;
  severity?: RiskLevel;
  target_closure_date?: string | null;
  evidence_reviewed?: string[] | null;
  evidence_gaps?: string | null;
}

export interface Gap {
  id: string;
  tenant_id: string;
  assessment_id: string;
  requirement_id: string;
  gap_description: string;
  root_cause: string | null;
  impact_description: string | null;
  severity: RiskLevel;
  risk_score: number | null;
  current_status: ComplianceStatus;
  target_closure_date: string | null;
  identified_date: string;
  actual_closure_date: string | null;
  is_open: boolean;
  created_at: string;
}

// ============================================================================
// TYPES - ACTIONS
// ============================================================================

export interface ActionCreate {
  title: string;
  description?: string | null;
  action_type?: string | null;
  due_date: string;
  priority?: RequirementPriority;
  estimated_cost?: number | null;
  gap_id?: string | null;
  requirement_id?: string | null;
  responsible_id: string;
  department?: string | null;
}

export interface Action {
  id: string;
  tenant_id: string;
  number: string;
  title: string;
  description: string | null;
  action_type: string | null;
  gap_id: string | null;
  requirement_id: string | null;
  responsible_id: string;
  department: string | null;
  status: ActionStatus;
  priority: RequirementPriority;
  due_date: string;
  estimated_cost: number | null;
  progress_percent: number;
  start_date: string | null;
  completion_date: string | null;
  resolution_notes: string | null;
  verified_by: string | null;
  verified_at: string | null;
  actual_cost: number | null;
  created_at: string;
}

// ============================================================================
// TYPES - POLITIQUES
// ============================================================================

export interface PolicyCreate {
  code: string;
  name: string;
  description?: string | null;
  type?: DocumentType;
  category?: string | null;
  department?: string | null;
  content?: string | null;
  summary?: string | null;
  effective_date?: string | null;
  expiry_date?: string | null;
  requires_acknowledgment?: boolean;
  owner_id?: string | null;
  target_audience?: string[] | null;
}

export interface Policy {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  type: DocumentType;
  category: string | null;
  department: string | null;
  content: string | null;
  summary: string | null;
  version: string;
  version_date: string | null;
  effective_date: string | null;
  expiry_date: string | null;
  next_review_date: string | null;
  requires_acknowledgment: boolean;
  owner_id: string | null;
  approved_by: string | null;
  approved_at: string | null;
  is_published: boolean;
  is_active: boolean;
  file_name: string | null;
  acknowledgments_count: number;
  created_at: string;
}

export interface AcknowledgmentCreate {
  policy_id: string;
  notes?: string | null;
}

export interface Acknowledgment {
  id: string;
  tenant_id: string;
  policy_id: string;
  user_id: string;
  acknowledged_at: string;
  is_valid: boolean;
}

// ============================================================================
// TYPES - FORMATIONS
// ============================================================================

export interface TrainingCreate {
  code: string;
  name: string;
  description?: string | null;
  content_type?: string | null;
  duration_hours?: number | null;
  passing_score?: number | null;
  category?: string | null;
  is_mandatory?: boolean;
  recurrence_months?: number | null;
  regulation_id?: string | null;
  target_departments?: string[] | null;
  target_roles?: string[] | null;
  available_from?: string | null;
  available_until?: string | null;
  materials_url?: string | null;
  quiz_enabled?: boolean;
}

export interface Training {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  content_type: string | null;
  duration_hours: number | null;
  passing_score: number | null;
  category: string | null;
  is_mandatory: boolean;
  recurrence_months: number | null;
  regulation_id: string | null;
  target_departments: string[] | null;
  target_roles: string[] | null;
  available_from: string | null;
  available_until: string | null;
  is_active: boolean;
  materials_url: string | null;
  quiz_enabled: boolean;
  completions_count: number;
  created_at: string;
}

export interface CompletionCreate {
  training_id: string;
  user_id: string;
  assigned_date?: string | null;
  due_date?: string | null;
}

export interface Completion {
  id: string;
  tenant_id: string;
  training_id: string;
  user_id: string;
  assigned_date: string | null;
  due_date: string | null;
  started_at: string | null;
  completed_at: string | null;
  score: number | null;
  passed: boolean | null;
  attempts: number;
  certificate_number: string | null;
  expiry_date: string | null;
  is_current: boolean;
}

// ============================================================================
// TYPES - AUDITS
// ============================================================================

export interface AuditCreate {
  name: string;
  audit_type: string;
  description?: string | null;
  scope?: string | null;
  planned_start?: string | null;
  planned_end?: string | null;
  regulation_id?: string | null;
  departments?: string[] | null;
  lead_auditor_id?: string | null;
  auditor_ids?: string[] | null;
  auditee_ids?: string[] | null;
}

export interface Audit {
  id: string;
  tenant_id: string;
  number: string;
  name: string;
  description: string | null;
  audit_type: string;
  scope: string | null;
  regulation_id: string | null;
  departments: string[] | null;
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  status: AuditStatus;
  lead_auditor_id: string | null;
  total_findings: number;
  critical_findings: number;
  major_findings: number;
  minor_findings: number;
  observations: number;
  executive_summary: string | null;
  conclusions: string | null;
  recommendations: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - CONSTATATIONS
// ============================================================================

export interface FindingCreate {
  audit_id: string;
  title: string;
  description: string;
  severity?: FindingSeverity;
  category?: string | null;
  evidence?: string | null;
  root_cause?: string | null;
  recommendation?: string | null;
  requirement_id?: string | null;
  response_due_date?: string | null;
  responsible_id?: string | null;
}

export interface Finding {
  id: string;
  tenant_id: string;
  number: string;
  audit_id: string;
  requirement_id: string | null;
  title: string;
  description: string;
  severity: FindingSeverity;
  category: string | null;
  evidence: string | null;
  root_cause: string | null;
  recommendation: string | null;
  identified_date: string;
  response_due_date: string | null;
  closure_date: string | null;
  responsible_id: string | null;
  is_closed: boolean;
  response: string | null;
  response_date: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - RISQUES
// ============================================================================

export interface RiskCreate {
  code: string;
  title: string;
  description?: string | null;
  category?: string | null;
  likelihood: number;
  impact: number;
  regulation_id?: string | null;
  treatment_strategy?: string | null;
  treatment_description?: string | null;
  current_controls?: string | null;
  planned_controls?: string | null;
  owner_id?: string | null;
  department?: string | null;
}

export interface RiskUpdate {
  title?: string;
  description?: string | null;
  category?: string | null;
  likelihood?: number;
  impact?: number;
  residual_likelihood?: number | null;
  residual_impact?: number | null;
  treatment_strategy?: string | null;
  treatment_description?: string | null;
  current_controls?: string | null;
  planned_controls?: string | null;
  owner_id?: string | null;
  is_accepted?: boolean;
  is_active?: boolean;
}

export interface Risk {
  id: string;
  tenant_id: string;
  code: string;
  title: string;
  description: string | null;
  category: string | null;
  likelihood: number;
  impact: number;
  risk_score: number;
  risk_level: RiskLevel;
  residual_likelihood: number | null;
  residual_impact: number | null;
  residual_score: number | null;
  residual_level: RiskLevel | null;
  regulation_id: string | null;
  treatment_strategy: string | null;
  treatment_description: string | null;
  current_controls: string | null;
  planned_controls: string | null;
  owner_id: string | null;
  department: string | null;
  identified_date: string;
  last_review_date: string | null;
  next_review_date: string | null;
  is_active: boolean;
  is_accepted: boolean;
  created_at: string;
}

// ============================================================================
// TYPES - INCIDENTS
// ============================================================================

export interface IncidentCreate {
  title: string;
  description: string;
  incident_type?: string | null;
  severity?: IncidentSeverity;
  incident_date: string;
  regulation_id?: string | null;
  department?: string | null;
}

export interface Incident {
  id: string;
  tenant_id: string;
  number: string;
  title: string;
  description: string;
  incident_type: string | null;
  severity: IncidentSeverity;
  incident_date: string;
  regulation_id: string | null;
  reporter_id: string;
  assigned_to: string | null;
  department: string | null;
  status: IncidentStatus;
  reported_date: string;
  resolved_date: string | null;
  closed_date: string | null;
  investigation_notes: string | null;
  root_cause: string | null;
  resolution: string | null;
  requires_disclosure: boolean;
  created_at: string;
}

// ============================================================================
// TYPES - RAPPORTS
// ============================================================================

export interface ReportCreate {
  name: string;
  type: ReportType;
  description?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  regulation_ids?: string[] | null;
  department_ids?: string[] | null;
}

export interface Report {
  id: string;
  tenant_id: string;
  number: string;
  name: string;
  description: string | null;
  type: ReportType;
  period_start: string | null;
  period_end: string | null;
  executive_summary: string | null;
  content: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  file_name: string | null;
  is_published: boolean;
  published_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - MÉTRIQUES
// ============================================================================

export interface ComplianceMetrics {
  overall_compliance_rate: number;
  compliant_requirements: number;
  non_compliant_requirements: number;
  partial_requirements: number;
  pending_requirements: number;
  total_requirements: number;
  open_gaps: number;
  open_actions: number;
  overdue_actions: number;
  active_audits: number;
  open_findings: number;
  critical_findings: number;
  active_risks: number;
  high_risks: number;
  critical_risks: number;
  open_incidents: number;
  training_compliance_rate: number;
  policies_requiring_acknowledgment: number;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/compliance';

export const complianceApi = {
  // --------------------------------------------------------------------------
  // Métriques
  // --------------------------------------------------------------------------
  getMetrics: () =>
    api.get<ComplianceMetrics>(`${BASE_PATH}/metrics`),

  // --------------------------------------------------------------------------
  // Réglementations
  // --------------------------------------------------------------------------
  createRegulation: (data: RegulationCreate) =>
    api.post<Regulation>(`${BASE_PATH}/regulations`, data),

  listRegulations: (params?: {
    regulation_type?: RegulationType;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Regulation[]>(`${BASE_PATH}/regulations${buildQueryString(params || {})}`),

  getRegulation: (regulationId: string) =>
    api.get<Regulation>(`${BASE_PATH}/regulations/${regulationId}`),

  updateRegulation: (regulationId: string, data: RegulationUpdate) =>
    api.put<Regulation>(`${BASE_PATH}/regulations/${regulationId}`, data),

  // --------------------------------------------------------------------------
  // Exigences
  // --------------------------------------------------------------------------
  createRequirement: (data: RequirementCreate) =>
    api.post<Requirement>(`${BASE_PATH}/requirements`, data),

  listRequirements: (params?: {
    regulation_id?: string;
    compliance_status?: ComplianceStatus;
    priority?: RequirementPriority;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Requirement[]>(`${BASE_PATH}/requirements${buildQueryString(params || {})}`),

  getRequirement: (requirementId: string) =>
    api.get<Requirement>(`${BASE_PATH}/requirements/${requirementId}`),

  updateRequirement: (requirementId: string, data: RequirementUpdate) =>
    api.put<Requirement>(`${BASE_PATH}/requirements/${requirementId}`, data),

  assessRequirement: (requirementId: string, status: ComplianceStatus, score?: number) =>
    api.post<Requirement>(`${BASE_PATH}/requirements/${requirementId}/assess${buildQueryString({ status, score })}`),

  // --------------------------------------------------------------------------
  // Évaluations
  // --------------------------------------------------------------------------
  createAssessment: (data: AssessmentCreate) =>
    api.post<Assessment>(`${BASE_PATH}/assessments`, data),

  getAssessment: (assessmentId: string) =>
    api.get<Assessment>(`${BASE_PATH}/assessments/${assessmentId}`),

  startAssessment: (assessmentId: string) =>
    api.post<Assessment>(`${BASE_PATH}/assessments/${assessmentId}/start`),

  completeAssessment: (assessmentId: string, findingsSummary?: string, recommendations?: string) =>
    api.post<Assessment>(`${BASE_PATH}/assessments/${assessmentId}/complete${buildQueryString({
      findings_summary: findingsSummary,
      recommendations,
    })}`),

  approveAssessment: (assessmentId: string) =>
    api.post<Assessment>(`${BASE_PATH}/assessments/${assessmentId}/approve`),

  // --------------------------------------------------------------------------
  // Écarts
  // --------------------------------------------------------------------------
  createGap: (data: GapCreate) =>
    api.post<Gap>(`${BASE_PATH}/gaps`, data),

  closeGap: (gapId: string) =>
    api.post<Gap>(`${BASE_PATH}/gaps/${gapId}/close`),

  // --------------------------------------------------------------------------
  // Actions
  // --------------------------------------------------------------------------
  createAction: (data: ActionCreate) =>
    api.post<Action>(`${BASE_PATH}/actions`, data),

  getAction: (actionId: string) =>
    api.get<Action>(`${BASE_PATH}/actions/${actionId}`),

  startAction: (actionId: string) =>
    api.post<Action>(`${BASE_PATH}/actions/${actionId}/start`),

  completeAction: (actionId: string, resolutionNotes: string, evidence?: string[], actualCost?: number) =>
    api.post<Action>(`${BASE_PATH}/actions/${actionId}/complete${buildQueryString({
      resolution_notes: resolutionNotes,
      actual_cost: actualCost,
    })}`, evidence ? { evidence } : undefined),

  verifyAction: (actionId: string, verificationNotes?: string) =>
    api.post<Action>(`${BASE_PATH}/actions/${actionId}/verify${buildQueryString({
      verification_notes: verificationNotes,
    })}`),

  getOverdueActions: () =>
    api.get<Action[]>(`${BASE_PATH}/actions/overdue`),

  // --------------------------------------------------------------------------
  // Politiques
  // --------------------------------------------------------------------------
  createPolicy: (data: PolicyCreate) =>
    api.post<Policy>(`${BASE_PATH}/policies`, data),

  listPolicies: (params?: {
    is_published?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Policy[]>(`${BASE_PATH}/policies${buildQueryString(params || {})}`),

  getPolicy: (policyId: string) =>
    api.get<Policy>(`${BASE_PATH}/policies/${policyId}`),

  publishPolicy: (policyId: string) =>
    api.post<Policy>(`${BASE_PATH}/policies/${policyId}/publish`),

  acknowledgePolicy: (data: AcknowledgmentCreate) =>
    api.post<Acknowledgment>(`${BASE_PATH}/policies/acknowledge`, data),

  // --------------------------------------------------------------------------
  // Formations
  // --------------------------------------------------------------------------
  createTraining: (data: TrainingCreate) =>
    api.post<Training>(`${BASE_PATH}/trainings`, data),

  getTraining: (trainingId: string) =>
    api.get<Training>(`${BASE_PATH}/trainings/${trainingId}`),

  assignTraining: (data: CompletionCreate) =>
    api.post<Completion>(`${BASE_PATH}/trainings/assign`, data),

  startTrainingCompletion: (completionId: string) =>
    api.post<Completion>(`${BASE_PATH}/trainings/completions/${completionId}/start`),

  completeTrainingCompletion: (completionId: string, score: number, certificateNumber?: string) =>
    api.post<Completion>(`${BASE_PATH}/trainings/completions/${completionId}/complete${buildQueryString({
      score,
      certificate_number: certificateNumber,
    })}`),

  // --------------------------------------------------------------------------
  // Audits
  // --------------------------------------------------------------------------
  createAudit: (data: AuditCreate) =>
    api.post<Audit>(`${BASE_PATH}/audits`, data),

  getAudit: (auditId: string) =>
    api.get<Audit>(`${BASE_PATH}/audits/${auditId}`),

  startAudit: (auditId: string) =>
    api.post<Audit>(`${BASE_PATH}/audits/${auditId}/start`),

  completeAudit: (auditId: string, executiveSummary?: string, conclusions?: string, recommendations?: string) =>
    api.post<Audit>(`${BASE_PATH}/audits/${auditId}/complete${buildQueryString({
      executive_summary: executiveSummary,
      conclusions,
      recommendations,
    })}`),

  closeAudit: (auditId: string) =>
    api.post<Audit>(`${BASE_PATH}/audits/${auditId}/close`),

  // --------------------------------------------------------------------------
  // Constatations
  // --------------------------------------------------------------------------
  createFinding: (data: FindingCreate) =>
    api.post<Finding>(`${BASE_PATH}/findings`, data),

  respondToFinding: (findingId: string, response: string) =>
    api.post<Finding>(`${BASE_PATH}/findings/${findingId}/respond${buildQueryString({ response })}`),

  closeFinding: (findingId: string) =>
    api.post<Finding>(`${BASE_PATH}/findings/${findingId}/close`),

  // --------------------------------------------------------------------------
  // Risques
  // --------------------------------------------------------------------------
  createRisk: (data: RiskCreate) =>
    api.post<Risk>(`${BASE_PATH}/risks`, data),

  getRisk: (riskId: string) =>
    api.get<Risk>(`${BASE_PATH}/risks/${riskId}`),

  updateRisk: (riskId: string, data: RiskUpdate) =>
    api.put<Risk>(`${BASE_PATH}/risks/${riskId}`, data),

  acceptRisk: (riskId: string) =>
    api.post<Risk>(`${BASE_PATH}/risks/${riskId}/accept`),

  // --------------------------------------------------------------------------
  // Incidents
  // --------------------------------------------------------------------------
  createIncident: (data: IncidentCreate) =>
    api.post<Incident>(`${BASE_PATH}/incidents`, data),

  getIncident: (incidentId: string) =>
    api.get<Incident>(`${BASE_PATH}/incidents/${incidentId}`),

  assignIncident: (incidentId: string, assigneeId: string) =>
    api.post<Incident>(`${BASE_PATH}/incidents/${incidentId}/assign${buildQueryString({ assignee_id: assigneeId })}`),

  resolveIncident: (incidentId: string, resolution: string, rootCause?: string, lessonsLearned?: string) =>
    api.post<Incident>(`${BASE_PATH}/incidents/${incidentId}/resolve${buildQueryString({
      resolution,
      root_cause: rootCause,
      lessons_learned: lessonsLearned,
    })}`),

  closeIncident: (incidentId: string) =>
    api.post<Incident>(`${BASE_PATH}/incidents/${incidentId}/close`),

  // --------------------------------------------------------------------------
  // Rapports
  // --------------------------------------------------------------------------
  createReport: (data: ReportCreate) =>
    api.post<Report>(`${BASE_PATH}/reports`, data),

  publishReport: (reportId: string) =>
    api.post<Report>(`${BASE_PATH}/reports/${reportId}/publish`),
};

export default complianceApi;
