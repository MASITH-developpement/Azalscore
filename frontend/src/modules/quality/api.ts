/**
 * AZALSCORE - Quality Management API
 * ===================================
 * Complete typed API client for quality module.
 * Covers: Non-conformances, Controls, Audits, CAPA, Claims, Indicators, Certifications
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type NonConformanceType =
  | 'PRODUCT'
  | 'PROCESS'
  | 'SERVICE'
  | 'SUPPLIER'
  | 'CUSTOMER'
  | 'INTERNAL'
  | 'EXTERNAL'
  | 'AUDIT'
  | 'REGULATORY';

export type NonConformanceStatus =
  | 'DRAFT'
  | 'OPEN'
  | 'UNDER_ANALYSIS'
  | 'ACTION_REQUIRED'
  | 'IN_PROGRESS'
  | 'VERIFICATION'
  | 'CLOSED'
  | 'CANCELLED';

export type NonConformanceSeverity = 'MINOR' | 'MAJOR' | 'CRITICAL' | 'BLOCKING';

export type ControlType =
  | 'INCOMING'
  | 'IN_PROCESS'
  | 'FINAL'
  | 'OUTGOING'
  | 'SAMPLING'
  | 'DESTRUCTIVE'
  | 'NON_DESTRUCTIVE'
  | 'VISUAL'
  | 'DIMENSIONAL'
  | 'FUNCTIONAL'
  | 'LABORATORY';

export type ControlStatus = 'PLANNED' | 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type ControlResult = 'PASSED' | 'FAILED' | 'CONDITIONAL' | 'PENDING' | 'NOT_APPLICABLE';

export type AuditType =
  | 'INTERNAL'
  | 'EXTERNAL'
  | 'SUPPLIER'
  | 'CUSTOMER'
  | 'CERTIFICATION'
  | 'SURVEILLANCE'
  | 'PROCESS'
  | 'PRODUCT'
  | 'SYSTEM';

export type AuditStatus =
  | 'PLANNED'
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'REPORT_PENDING'
  | 'CLOSED'
  | 'CANCELLED';

export type FindingSeverity = 'OBSERVATION' | 'MINOR' | 'MAJOR' | 'CRITICAL';

export type CAPAType = 'CORRECTIVE' | 'PREVENTIVE' | 'IMPROVEMENT';

export type CAPAStatus =
  | 'DRAFT'
  | 'OPEN'
  | 'ANALYSIS'
  | 'ACTION_PLANNING'
  | 'IN_PROGRESS'
  | 'VERIFICATION'
  | 'CLOSED_EFFECTIVE'
  | 'CLOSED_INEFFECTIVE'
  | 'CANCELLED';

export type ClaimStatus =
  | 'RECEIVED'
  | 'ACKNOWLEDGED'
  | 'UNDER_INVESTIGATION'
  | 'PENDING_RESPONSE'
  | 'RESPONSE_SENT'
  | 'IN_RESOLUTION'
  | 'RESOLVED'
  | 'CLOSED'
  | 'REJECTED';

export type CertificationStatus =
  | 'PLANNED'
  | 'IN_PREPARATION'
  | 'AUDIT_SCHEDULED'
  | 'AUDIT_COMPLETED'
  | 'CERTIFIED'
  | 'SUSPENDED'
  | 'WITHDRAWN'
  | 'EXPIRED';

// ============================================================================
// COMMON TYPES
// ============================================================================

export interface Attachment {
  file_name: string;
  file_url: string;
  file_size?: number | null;
  mime_type?: string | null;
  uploaded_by?: number | null;
  uploaded_at?: string | null;
  description?: string | null;
}

export interface AttachmentCreate {
  file_name: string;
  file_url: string;
  file_size?: number | null;
  mime_type?: string | null;
  description?: string | null;
}

// ============================================================================
// NON-CONFORMANCES
// ============================================================================

export interface NonConformanceAction {
  id: number;
  nc_id: number;
  action_number: number;
  action_type: string;
  description: string;
  responsible_id?: number | null;
  planned_date?: string | null;
  due_date?: string | null;
  completed_date?: string | null;
  status: string;
  verified: boolean;
  verified_date?: string | null;
  comments?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NonConformance {
  id: number;
  nc_number: string;
  title: string;
  description?: string | null;
  nc_type: NonConformanceType;
  severity: NonConformanceSeverity;
  status: NonConformanceStatus;
  detected_date: string;
  detection_location?: string | null;
  detection_phase?: string | null;
  detected_by_id?: number | null;
  source_type?: string | null;
  source_reference?: string | null;
  product_id?: number | null;
  lot_number?: string | null;
  quantity_affected?: string | null;
  supplier_id?: number | null;
  customer_id?: number | null;
  immediate_cause?: string | null;
  root_cause?: string | null;
  cause_analysis_method?: string | null;
  impact_description?: string | null;
  estimated_cost?: string | null;
  actual_cost?: string | null;
  immediate_action?: string | null;
  disposition?: string | null;
  responsible_id?: number | null;
  department?: string | null;
  capa_required: boolean;
  capa_id?: number | null;
  closed_date?: string | null;
  effectiveness_verified: boolean;
  is_recurrent: boolean;
  recurrence_count: number;
  actions: NonConformanceAction[];
  attachments: Attachment[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface NonConformanceCreate {
  title: string;
  description?: string | null;
  nc_type: NonConformanceType;
  severity: NonConformanceSeverity;
  detected_date: string;
  detection_location?: string | null;
  detection_phase?: string | null;
  source_type?: string | null;
  source_reference?: string | null;
  source_id?: number | null;
  product_id?: number | null;
  lot_number?: string | null;
  serial_number?: string | null;
  quantity_affected?: string | null;
  unit_id?: number | null;
  supplier_id?: number | null;
  customer_id?: number | null;
  immediate_action?: string | null;
  responsible_id?: number | null;
  department?: string | null;
  notes?: string | null;
}

export interface NonConformanceUpdate {
  title?: string | null;
  description?: string | null;
  severity?: NonConformanceSeverity | null;
  status?: NonConformanceStatus | null;
  immediate_cause?: string | null;
  root_cause?: string | null;
  cause_analysis_method?: string | null;
  impact_description?: string | null;
  estimated_cost?: string | null;
  actual_cost?: string | null;
  immediate_action?: string | null;
  disposition?: string | null;
  disposition_justification?: string | null;
  capa_required?: boolean | null;
  capa_id?: number | null;
  responsible_id?: number | null;
  department?: string | null;
  notes?: string | null;
}

export interface NonConformanceClose {
  closure_justification: string;
  effectiveness_verified?: boolean;
}

export interface NonConformanceActionCreate {
  action_type: string;
  description: string;
  responsible_id?: number | null;
  planned_date?: string | null;
  due_date?: string | null;
  comments?: string | null;
}

export interface NonConformanceActionUpdate {
  description?: string | null;
  responsible_id?: number | null;
  due_date?: string | null;
  status?: string | null;
  completed_date?: string | null;
  comments?: string | null;
}

export interface NonConformanceList {
  items: NonConformance[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// CONTROL TEMPLATES
// ============================================================================

export interface ControlTemplateItem {
  id: number;
  template_id: number;
  sequence: number;
  characteristic: string;
  description?: string | null;
  measurement_type: string;
  unit?: string | null;
  nominal_value?: string | null;
  tolerance_min?: string | null;
  tolerance_max?: string | null;
  upper_limit?: string | null;
  lower_limit?: string | null;
  expected_result?: string | null;
  measurement_method?: string | null;
  equipment_code?: string | null;
  is_critical: boolean;
  is_mandatory: boolean;
  sampling_frequency?: string | null;
  created_at: string;
}

export interface ControlTemplateItemCreate {
  sequence: number;
  characteristic: string;
  description?: string | null;
  measurement_type: string;
  unit?: string | null;
  nominal_value?: string | null;
  tolerance_min?: string | null;
  tolerance_max?: string | null;
  expected_result?: string | null;
  measurement_method?: string | null;
  equipment_code?: string | null;
  is_critical?: boolean;
  is_mandatory?: boolean;
  sampling_frequency?: string | null;
}

export interface ControlTemplate {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  version: string;
  control_type: ControlType;
  applies_to?: string | null;
  product_category_id?: number | null;
  instructions?: string | null;
  sampling_plan?: string | null;
  acceptance_criteria?: string | null;
  estimated_duration_minutes?: number | null;
  required_equipment?: string[] | null;
  is_active: boolean;
  valid_from?: string | null;
  valid_until?: string | null;
  items: ControlTemplateItem[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface ControlTemplateCreate {
  code: string;
  name: string;
  description?: string | null;
  version?: string;
  control_type: ControlType;
  applies_to?: string | null;
  product_category_id?: number | null;
  instructions?: string | null;
  sampling_plan?: string | null;
  acceptance_criteria?: string | null;
  estimated_duration_minutes?: number | null;
  required_equipment?: string[] | null;
  items?: ControlTemplateItemCreate[] | null;
}

export interface ControlTemplateUpdate {
  name?: string | null;
  description?: string | null;
  version?: string | null;
  instructions?: string | null;
  sampling_plan?: string | null;
  acceptance_criteria?: string | null;
  estimated_duration_minutes?: number | null;
  is_active?: boolean | null;
}

export interface ControlTemplateList {
  items: ControlTemplate[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// QUALITY CONTROLS
// ============================================================================

export interface ControlLine {
  id: number;
  control_id: number;
  template_item_id?: number | null;
  sequence: number;
  characteristic: string;
  nominal_value?: string | null;
  tolerance_min?: string | null;
  tolerance_max?: string | null;
  unit?: string | null;
  measured_value?: string | null;
  measured_text?: string | null;
  measured_boolean?: boolean | null;
  measurement_date?: string | null;
  result?: ControlResult | null;
  deviation?: string | null;
  equipment_code?: string | null;
  comments?: string | null;
  created_at: string;
}

export interface ControlLineCreate {
  sequence: number;
  characteristic: string;
  nominal_value?: string | null;
  tolerance_min?: string | null;
  tolerance_max?: string | null;
  unit?: string | null;
  template_item_id?: number | null;
  measured_value?: string | null;
  measured_text?: string | null;
  measured_boolean?: boolean | null;
  result?: ControlResult | null;
  equipment_code?: string | null;
  comments?: string | null;
}

export interface ControlLineUpdate {
  measured_value?: string | null;
  measured_text?: string | null;
  measured_boolean?: boolean | null;
  result?: ControlResult | null;
  equipment_code?: string | null;
  comments?: string | null;
}

export interface QualityControl {
  id: number;
  control_number: string;
  control_type: ControlType;
  control_date: string;
  template_id?: number | null;
  source_type?: string | null;
  source_reference?: string | null;
  product_id?: number | null;
  lot_number?: string | null;
  serial_number?: string | null;
  quantity_to_control?: string | null;
  quantity_controlled?: string | null;
  quantity_conforming?: string | null;
  quantity_non_conforming?: string | null;
  supplier_id?: number | null;
  customer_id?: number | null;
  start_time?: string | null;
  end_time?: string | null;
  location?: string | null;
  controller_id?: number | null;
  status: ControlStatus;
  result?: ControlResult | null;
  result_date?: string | null;
  decision?: string | null;
  decision_by_id?: number | null;
  decision_date?: string | null;
  decision_comments?: string | null;
  nc_id?: number | null;
  observations?: string | null;
  lines: ControlLine[];
  attachments: Attachment[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface QualityControlCreate {
  control_type: ControlType;
  control_date: string;
  template_id?: number | null;
  source_type?: string | null;
  source_reference?: string | null;
  source_id?: number | null;
  product_id?: number | null;
  lot_number?: string | null;
  serial_number?: string | null;
  quantity_to_control?: string | null;
  unit_id?: number | null;
  supplier_id?: number | null;
  customer_id?: number | null;
  location?: string | null;
  controller_id?: number | null;
  observations?: string | null;
  lines?: ControlLineCreate[] | null;
}

export interface QualityControlUpdate {
  control_date?: string | null;
  quantity_controlled?: string | null;
  quantity_conforming?: string | null;
  quantity_non_conforming?: string | null;
  location?: string | null;
  controller_id?: number | null;
  status?: ControlStatus | null;
  result?: ControlResult | null;
  decision?: string | null;
  decision_comments?: string | null;
  observations?: string | null;
}

export interface QualityControlList {
  items: QualityControl[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// AUDITS
// ============================================================================

export interface AuditFinding {
  id: number;
  audit_id: number;
  finding_number: number;
  title: string;
  description: string;
  severity: FindingSeverity;
  category?: string | null;
  clause_reference?: string | null;
  process_reference?: string | null;
  evidence?: string | null;
  risk_description?: string | null;
  risk_level?: string | null;
  capa_required: boolean;
  capa_id?: number | null;
  auditee_response?: string | null;
  response_date?: string | null;
  action_due_date?: string | null;
  action_completed_date?: string | null;
  status: string;
  verified: boolean;
  verified_date?: string | null;
  verification_comments?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditFindingCreate {
  title: string;
  description: string;
  severity: FindingSeverity;
  category?: string | null;
  clause_reference?: string | null;
  process_reference?: string | null;
  evidence?: string | null;
  risk_description?: string | null;
  capa_required?: boolean;
  action_due_date?: string | null;
}

export interface AuditFindingUpdate {
  title?: string | null;
  description?: string | null;
  severity?: FindingSeverity | null;
  category?: string | null;
  evidence?: string | null;
  risk_description?: string | null;
  auditee_response?: string | null;
  action_due_date?: string | null;
  status?: string | null;
  capa_id?: number | null;
}

export interface Audit {
  id: number;
  audit_number: string;
  title: string;
  description?: string | null;
  audit_type: AuditType;
  reference_standard?: string | null;
  reference_version?: string | null;
  audit_scope?: string | null;
  planned_date?: string | null;
  planned_end_date?: string | null;
  actual_date?: string | null;
  actual_end_date?: string | null;
  status: AuditStatus;
  lead_auditor_id?: number | null;
  auditors?: number[] | null;
  audited_entity?: string | null;
  audited_department?: string | null;
  auditee_contact_id?: number | null;
  supplier_id?: number | null;
  total_findings: number;
  critical_findings: number;
  major_findings: number;
  minor_findings: number;
  observations: number;
  overall_score?: string | null;
  max_score?: string | null;
  audit_conclusion?: string | null;
  recommendation?: string | null;
  report_date?: string | null;
  report_file?: string | null;
  follow_up_required: boolean;
  follow_up_date?: string | null;
  follow_up_completed: boolean;
  closed_date?: string | null;
  findings: AuditFinding[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface AuditCreate {
  title: string;
  description?: string | null;
  audit_type: AuditType;
  reference_standard?: string | null;
  reference_version?: string | null;
  audit_scope?: string | null;
  planned_date?: string | null;
  planned_end_date?: string | null;
  lead_auditor_id?: number | null;
  auditors?: number[] | null;
  audited_entity?: string | null;
  audited_department?: string | null;
  auditee_contact_id?: number | null;
  supplier_id?: number | null;
}

export interface AuditUpdate {
  title?: string | null;
  description?: string | null;
  audit_scope?: string | null;
  planned_date?: string | null;
  planned_end_date?: string | null;
  actual_date?: string | null;
  actual_end_date?: string | null;
  status?: AuditStatus | null;
  lead_auditor_id?: number | null;
  auditors?: number[] | null;
  audited_entity?: string | null;
  audited_department?: string | null;
  overall_score?: string | null;
  max_score?: string | null;
  audit_conclusion?: string | null;
  recommendation?: string | null;
  follow_up_required?: boolean | null;
  follow_up_date?: string | null;
}

export interface AuditClose {
  audit_conclusion: string;
  recommendation?: string | null;
}

export interface AuditList {
  items: Audit[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// CAPA
// ============================================================================

export interface CAPAAction {
  id: number;
  capa_id: number;
  action_number: number;
  action_type: string;
  description: string;
  responsible_id?: number | null;
  due_date: string;
  planned_date?: string | null;
  completed_date?: string | null;
  status: string;
  result?: string | null;
  evidence?: string | null;
  verification_required: boolean;
  verified: boolean;
  verified_date?: string | null;
  verification_result?: string | null;
  estimated_cost?: string | null;
  actual_cost?: string | null;
  comments?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CAPAActionCreate {
  action_type: string;
  description: string;
  responsible_id?: number | null;
  due_date: string;
  planned_date?: string | null;
  verification_required?: boolean;
  estimated_cost?: string | null;
}

export interface CAPAActionUpdate {
  description?: string | null;
  responsible_id?: number | null;
  due_date?: string | null;
  status?: string | null;
  completed_date?: string | null;
  result?: string | null;
  evidence?: string | null;
  actual_cost?: string | null;
  comments?: string | null;
}

export interface CAPA {
  id: number;
  capa_number: string;
  title: string;
  description: string;
  capa_type: CAPAType;
  source_type?: string | null;
  source_reference?: string | null;
  status: CAPAStatus;
  priority: string;
  open_date: string;
  target_close_date?: string | null;
  actual_close_date?: string | null;
  owner_id: number;
  department?: string | null;
  problem_statement?: string | null;
  immediate_containment?: string | null;
  root_cause_analysis?: string | null;
  root_cause_method?: string | null;
  root_cause_verified: boolean;
  impact_assessment?: string | null;
  risk_level?: string | null;
  effectiveness_criteria?: string | null;
  effectiveness_verified: boolean;
  effectiveness_date?: string | null;
  effectiveness_result?: string | null;
  extension_required: boolean;
  extension_scope?: string | null;
  extension_completed: boolean;
  closure_comments?: string | null;
  actions: CAPAAction[];
  attachments: Attachment[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface CAPACreate {
  title: string;
  description: string;
  capa_type: CAPAType;
  source_type?: string | null;
  source_reference?: string | null;
  source_id?: number | null;
  priority?: string;
  open_date: string;
  target_close_date?: string | null;
  owner_id: number;
  department?: string | null;
  problem_statement?: string | null;
  immediate_containment?: string | null;
  effectiveness_criteria?: string | null;
}

export interface CAPAUpdate {
  title?: string | null;
  description?: string | null;
  priority?: string | null;
  status?: CAPAStatus | null;
  target_close_date?: string | null;
  owner_id?: number | null;
  department?: string | null;
  problem_statement?: string | null;
  immediate_containment?: string | null;
  root_cause_analysis?: string | null;
  root_cause_method?: string | null;
  root_cause_verified?: boolean | null;
  impact_assessment?: string | null;
  risk_level?: string | null;
  effectiveness_criteria?: string | null;
  extension_required?: boolean | null;
  extension_scope?: string | null;
}

export interface CAPAClose {
  effectiveness_verified: boolean;
  effectiveness_result: string;
  closure_comments?: string | null;
}

export interface CAPAList {
  items: CAPA[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// CUSTOMER CLAIMS
// ============================================================================

export interface ClaimAction {
  id: number;
  claim_id: number;
  action_number: number;
  action_type: string;
  description: string;
  responsible_id?: number | null;
  due_date?: string | null;
  completed_date?: string | null;
  status: string;
  result?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClaimActionCreate {
  action_type: string;
  description: string;
  responsible_id?: number | null;
  due_date?: string | null;
}

export interface CustomerClaim {
  id: number;
  claim_number: string;
  title: string;
  description: string;
  customer_id: number;
  customer_contact?: string | null;
  customer_reference?: string | null;
  received_date: string;
  received_via?: string | null;
  received_by_id?: number | null;
  product_id?: number | null;
  order_reference?: string | null;
  invoice_reference?: string | null;
  lot_number?: string | null;
  quantity_affected?: string | null;
  claim_type?: string | null;
  severity?: NonConformanceSeverity | null;
  priority: string;
  status: ClaimStatus;
  owner_id?: number | null;
  investigation_summary?: string | null;
  root_cause?: string | null;
  our_responsibility?: boolean | null;
  nc_id?: number | null;
  capa_id?: number | null;
  response_due_date?: string | null;
  response_date?: string | null;
  response_content?: string | null;
  resolution_type?: string | null;
  resolution_description?: string | null;
  resolution_date?: string | null;
  claim_amount?: string | null;
  accepted_amount?: string | null;
  customer_satisfied?: boolean | null;
  satisfaction_feedback?: string | null;
  closed_date?: string | null;
  actions: ClaimAction[];
  attachments: Attachment[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface CustomerClaimCreate {
  title: string;
  description: string;
  customer_id: number;
  received_date: string;
  customer_contact?: string | null;
  customer_reference?: string | null;
  received_via?: string | null;
  product_id?: number | null;
  order_reference?: string | null;
  invoice_reference?: string | null;
  lot_number?: string | null;
  quantity_affected?: string | null;
  claim_type?: string | null;
  severity?: NonConformanceSeverity | null;
  priority?: string;
  owner_id?: number | null;
  response_due_date?: string | null;
  claim_amount?: string | null;
}

export interface CustomerClaimUpdate {
  title?: string | null;
  description?: string | null;
  customer_contact?: string | null;
  severity?: NonConformanceSeverity | null;
  priority?: string | null;
  status?: ClaimStatus | null;
  owner_id?: number | null;
  investigation_summary?: string | null;
  root_cause?: string | null;
  our_responsibility?: boolean | null;
  nc_id?: number | null;
  capa_id?: number | null;
  response_due_date?: string | null;
  response_content?: string | null;
  resolution_type?: string | null;
  resolution_description?: string | null;
  claim_amount?: string | null;
  accepted_amount?: string | null;
}

export interface ClaimRespond {
  response_content: string;
}

export interface ClaimResolve {
  resolution_type: string;
  resolution_description: string;
  accepted_amount?: string | null;
}

export interface ClaimClose {
  customer_satisfied?: boolean | null;
  satisfaction_feedback?: string | null;
}

export interface CustomerClaimList {
  items: CustomerClaim[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// QUALITY INDICATORS
// ============================================================================

export interface IndicatorMeasurement {
  id: number;
  indicator_id: number;
  measurement_date: string;
  value: string;
  period_start?: string | null;
  period_end?: string | null;
  numerator?: string | null;
  denominator?: string | null;
  target_value?: string | null;
  deviation?: string | null;
  achievement_rate?: string | null;
  status?: string | null;
  comments?: string | null;
  action_required: boolean;
  source?: string | null;
  created_at: string;
}

export interface IndicatorMeasurementCreate {
  measurement_date: string;
  value: string;
  period_start?: string | null;
  period_end?: string | null;
  numerator?: string | null;
  denominator?: string | null;
  comments?: string | null;
  source?: string;
}

export interface QualityIndicator {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  category?: string | null;
  formula?: string | null;
  unit?: string | null;
  target_value?: string | null;
  target_min?: string | null;
  target_max?: string | null;
  warning_threshold?: string | null;
  critical_threshold?: string | null;
  direction?: string | null;
  measurement_frequency?: string | null;
  data_source?: string | null;
  owner_id?: number | null;
  is_active: boolean;
  measurements: IndicatorMeasurement[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface QualityIndicatorCreate {
  code: string;
  name: string;
  description?: string | null;
  category?: string | null;
  formula?: string | null;
  unit?: string | null;
  target_value?: string | null;
  target_min?: string | null;
  target_max?: string | null;
  warning_threshold?: string | null;
  critical_threshold?: string | null;
  direction?: string | null;
  measurement_frequency?: string | null;
  data_source?: string | null;
  owner_id?: number | null;
}

export interface QualityIndicatorUpdate {
  name?: string | null;
  description?: string | null;
  category?: string | null;
  formula?: string | null;
  unit?: string | null;
  target_value?: string | null;
  target_min?: string | null;
  target_max?: string | null;
  warning_threshold?: string | null;
  critical_threshold?: string | null;
  direction?: string | null;
  measurement_frequency?: string | null;
  owner_id?: number | null;
  is_active?: boolean | null;
}

export interface QualityIndicatorList {
  items: QualityIndicator[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// CERTIFICATIONS
// ============================================================================

export interface CertificationAudit {
  id: number;
  certification_id: number;
  audit_type: string;
  audit_date: string;
  audit_end_date?: string | null;
  lead_auditor?: string | null;
  audit_team?: string[] | null;
  result?: string | null;
  findings_count: number;
  major_nc_count: number;
  minor_nc_count: number;
  observations_count: number;
  report_date?: string | null;
  report_file?: string | null;
  corrective_actions_due?: string | null;
  corrective_actions_closed?: string | null;
  follow_up_audit_date?: string | null;
  quality_audit_id?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CertificationAuditCreate {
  audit_type: string;
  audit_date: string;
  audit_end_date?: string | null;
  lead_auditor?: string | null;
  audit_team?: string[] | null;
  notes?: string | null;
}

export interface CertificationAuditUpdate {
  audit_date?: string | null;
  audit_end_date?: string | null;
  lead_auditor?: string | null;
  result?: string | null;
  findings_count?: number | null;
  major_nc_count?: number | null;
  minor_nc_count?: number | null;
  observations_count?: number | null;
  report_date?: string | null;
  report_file?: string | null;
  corrective_actions_due?: string | null;
  corrective_actions_closed?: string | null;
  follow_up_audit_date?: string | null;
  notes?: string | null;
}

export interface Certification {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  standard: string;
  standard_version?: string | null;
  scope?: string | null;
  certification_body?: string | null;
  certification_body_accreditation?: string | null;
  initial_certification_date?: string | null;
  current_certificate_date?: string | null;
  expiry_date?: string | null;
  next_surveillance_date?: string | null;
  next_renewal_date?: string | null;
  certificate_number?: string | null;
  certificate_file?: string | null;
  status: CertificationStatus;
  manager_id?: number | null;
  annual_cost?: string | null;
  audits: CertificationAudit[];
  notes?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface CertificationCreate {
  code: string;
  name: string;
  description?: string | null;
  standard: string;
  standard_version?: string | null;
  scope?: string | null;
  certification_body?: string | null;
  certification_body_accreditation?: string | null;
  initial_certification_date?: string | null;
  manager_id?: number | null;
  annual_cost?: string | null;
  notes?: string | null;
}

export interface CertificationUpdate {
  name?: string | null;
  description?: string | null;
  standard_version?: string | null;
  scope?: string | null;
  certification_body?: string | null;
  status?: CertificationStatus | null;
  current_certificate_date?: string | null;
  expiry_date?: string | null;
  certificate_number?: string | null;
  certificate_file?: string | null;
  next_surveillance_date?: string | null;
  next_renewal_date?: string | null;
  manager_id?: number | null;
  annual_cost?: string | null;
  notes?: string | null;
}

export interface CertificationList {
  items: Certification[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// DASHBOARD
// ============================================================================

export interface QualityDashboard {
  // Non-conformances
  nc_total: number;
  nc_open: number;
  nc_critical: number;
  nc_by_type: Record<string, number>;
  nc_by_status: Record<string, number>;
  // Quality controls
  controls_total: number;
  controls_completed: number;
  controls_pass_rate: string;
  controls_by_type: Record<string, number>;
  // Audits
  audits_planned: number;
  audits_completed: number;
  audit_findings_open: number;
  // CAPA
  capa_total: number;
  capa_open: number;
  capa_overdue: number;
  capa_effectiveness_rate: string;
  // Customer claims
  claims_total: number;
  claims_open: number;
  claims_avg_resolution_days?: string | null;
  claims_satisfaction_rate?: string | null;
  // Certifications
  certifications_active: number;
  certifications_expiring_soon: number;
  // Indicators
  indicators_on_target: number;
  indicators_warning: number;
  indicators_critical: number;
  // Trends
  nc_trend_30_days: Array<Record<string, unknown>>;
  control_trend_30_days: Array<Record<string, unknown>>;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/quality';

function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
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
// API CLIENT
// ============================================================================

export const qualityApi = {
  // ==========================================================================
  // Non-Conformances
  // ==========================================================================

  createNonConformance: (data: NonConformanceCreate) =>
    api.post<NonConformance>(`${BASE_PATH}/non-conformances`, data),

  listNonConformances: (params?: {
    skip?: number;
    limit?: number;
    nc_type?: NonConformanceType;
    status?: NonConformanceStatus;
    severity?: NonConformanceSeverity;
    date_from?: string;
    date_to?: string;
    search?: string;
  }) =>
    api.get<NonConformanceList>(
      `${BASE_PATH}/non-conformances${buildQueryString(params || {})}`
    ),

  getNonConformance: (ncId: number) =>
    api.get<NonConformance>(`${BASE_PATH}/non-conformances/${ncId}`),

  updateNonConformance: (ncId: number, data: NonConformanceUpdate) =>
    api.put<NonConformance>(`${BASE_PATH}/non-conformances/${ncId}`, data),

  openNonConformance: (ncId: number) =>
    api.post<NonConformance>(`${BASE_PATH}/non-conformances/${ncId}/open`, {}),

  closeNonConformance: (ncId: number, data: NonConformanceClose) =>
    api.post<NonConformance>(`${BASE_PATH}/non-conformances/${ncId}/close`, data),

  addNcAction: (ncId: number, data: NonConformanceActionCreate) =>
    api.post<NonConformanceAction>(`${BASE_PATH}/non-conformances/${ncId}/actions`, data),

  updateNcAction: (actionId: number, data: NonConformanceActionUpdate) =>
    api.put<NonConformanceAction>(`${BASE_PATH}/nc-actions/${actionId}`, data),

  // ==========================================================================
  // Control Templates
  // ==========================================================================

  createControlTemplate: (data: ControlTemplateCreate) =>
    api.post<ControlTemplate>(`${BASE_PATH}/control-templates`, data),

  listControlTemplates: (params?: {
    skip?: number;
    limit?: number;
    control_type?: ControlType;
    active_only?: boolean;
    search?: string;
  }) =>
    api.get<ControlTemplateList>(
      `${BASE_PATH}/control-templates${buildQueryString(params || {})}`
    ),

  getControlTemplate: (templateId: number) =>
    api.get<ControlTemplate>(`${BASE_PATH}/control-templates/${templateId}`),

  updateControlTemplate: (templateId: number, data: ControlTemplateUpdate) =>
    api.put<ControlTemplate>(`${BASE_PATH}/control-templates/${templateId}`, data),

  addTemplateItem: (templateId: number, data: ControlTemplateItemCreate) =>
    api.post<ControlTemplateItem>(
      `${BASE_PATH}/control-templates/${templateId}/items`,
      data
    ),

  // ==========================================================================
  // Quality Controls
  // ==========================================================================

  createControl: (data: QualityControlCreate) =>
    api.post<QualityControl>(`${BASE_PATH}/controls`, data),

  listControls: (params?: {
    skip?: number;
    limit?: number;
    control_type?: ControlType;
    status?: ControlStatus;
    result?: ControlResult;
    date_from?: string;
    date_to?: string;
    search?: string;
  }) =>
    api.get<QualityControlList>(
      `${BASE_PATH}/controls${buildQueryString(params || {})}`
    ),

  getControl: (controlId: number) =>
    api.get<QualityControl>(`${BASE_PATH}/controls/${controlId}`),

  updateControl: (controlId: number, data: QualityControlUpdate) =>
    api.put<QualityControl>(`${BASE_PATH}/controls/${controlId}`, data),

  startControl: (controlId: number) =>
    api.post<QualityControl>(`${BASE_PATH}/controls/${controlId}/start`, {}),

  updateControlLine: (lineId: number, data: ControlLineUpdate) =>
    api.put<QualityControl>(`${BASE_PATH}/control-lines/${lineId}`, data),

  completeControl: (controlId: number, decision: string, comments?: string) =>
    api.post<QualityControl>(
      `${BASE_PATH}/controls/${controlId}/complete${buildQueryString({ decision, comments })}`,
      {}
    ),

  // ==========================================================================
  // Audits
  // ==========================================================================

  createAudit: (data: AuditCreate) =>
    api.post<Audit>(`${BASE_PATH}/audits`, data),

  listAudits: (params?: {
    skip?: number;
    limit?: number;
    audit_type?: AuditType;
    status?: AuditStatus;
    date_from?: string;
    date_to?: string;
    search?: string;
  }) =>
    api.get<AuditList>(`${BASE_PATH}/audits${buildQueryString(params || {})}`),

  getAudit: (auditId: number) =>
    api.get<Audit>(`${BASE_PATH}/audits/${auditId}`),

  updateAudit: (auditId: number, data: AuditUpdate) =>
    api.put<Audit>(`${BASE_PATH}/audits/${auditId}`, data),

  startAudit: (auditId: number) =>
    api.post<Audit>(`${BASE_PATH}/audits/${auditId}/start`, {}),

  addFinding: (auditId: number, data: AuditFindingCreate) =>
    api.post<AuditFinding>(`${BASE_PATH}/audits/${auditId}/findings`, data),

  updateFinding: (findingId: number, data: AuditFindingUpdate) =>
    api.put<AuditFinding>(`${BASE_PATH}/audit-findings/${findingId}`, data),

  closeAudit: (auditId: number, data: AuditClose) =>
    api.post<Audit>(`${BASE_PATH}/audits/${auditId}/close`, data),

  // ==========================================================================
  // CAPA
  // ==========================================================================

  createCapa: (data: CAPACreate) =>
    api.post<CAPA>(`${BASE_PATH}/capas`, data),

  listCapas: (params?: {
    skip?: number;
    limit?: number;
    capa_type?: CAPAType;
    status?: CAPAStatus;
    priority?: string;
    owner_id?: number;
    search?: string;
  }) =>
    api.get<CAPAList>(`${BASE_PATH}/capas${buildQueryString(params || {})}`),

  getCapa: (capaId: number) =>
    api.get<CAPA>(`${BASE_PATH}/capas/${capaId}`),

  updateCapa: (capaId: number, data: CAPAUpdate) =>
    api.put<CAPA>(`${BASE_PATH}/capas/${capaId}`, data),

  addCapaAction: (capaId: number, data: CAPAActionCreate) =>
    api.post<CAPAAction>(`${BASE_PATH}/capas/${capaId}/actions`, data),

  updateCapaAction: (actionId: number, data: CAPAActionUpdate) =>
    api.put<CAPAAction>(`${BASE_PATH}/capa-actions/${actionId}`, data),

  closeCapa: (capaId: number, data: CAPAClose) =>
    api.post<CAPA>(`${BASE_PATH}/capas/${capaId}/close`, data),

  // ==========================================================================
  // Customer Claims
  // ==========================================================================

  createClaim: (data: CustomerClaimCreate) =>
    api.post<CustomerClaim>(`${BASE_PATH}/claims`, data),

  listClaims: (params?: {
    skip?: number;
    limit?: number;
    status?: ClaimStatus;
    customer_id?: number;
    date_from?: string;
    date_to?: string;
    search?: string;
  }) =>
    api.get<CustomerClaimList>(`${BASE_PATH}/claims${buildQueryString(params || {})}`),

  getClaim: (claimId: number) =>
    api.get<CustomerClaim>(`${BASE_PATH}/claims/${claimId}`),

  updateClaim: (claimId: number, data: CustomerClaimUpdate) =>
    api.put<CustomerClaim>(`${BASE_PATH}/claims/${claimId}`, data),

  acknowledgeClaim: (claimId: number) =>
    api.post<CustomerClaim>(`${BASE_PATH}/claims/${claimId}/acknowledge`, {}),

  respondClaim: (claimId: number, data: ClaimRespond) =>
    api.post<CustomerClaim>(`${BASE_PATH}/claims/${claimId}/respond`, data),

  resolveClaim: (claimId: number, data: ClaimResolve) =>
    api.post<CustomerClaim>(`${BASE_PATH}/claims/${claimId}/resolve`, data),

  closeClaim: (claimId: number, data: ClaimClose) =>
    api.post<CustomerClaim>(`${BASE_PATH}/claims/${claimId}/close`, data),

  addClaimAction: (claimId: number, data: ClaimActionCreate) =>
    api.post<ClaimAction>(`${BASE_PATH}/claims/${claimId}/actions`, data),

  // ==========================================================================
  // Quality Indicators
  // ==========================================================================

  createIndicator: (data: QualityIndicatorCreate) =>
    api.post<QualityIndicator>(`${BASE_PATH}/indicators`, data),

  listIndicators: (params?: {
    skip?: number;
    limit?: number;
    category?: string;
    active_only?: boolean;
    search?: string;
  }) =>
    api.get<QualityIndicatorList>(
      `${BASE_PATH}/indicators${buildQueryString(params || {})}`
    ),

  getIndicator: (indicatorId: number) =>
    api.get<QualityIndicator>(`${BASE_PATH}/indicators/${indicatorId}`),

  updateIndicator: (indicatorId: number, data: QualityIndicatorUpdate) =>
    api.put<QualityIndicator>(`${BASE_PATH}/indicators/${indicatorId}`, data),

  addMeasurement: (indicatorId: number, data: IndicatorMeasurementCreate) =>
    api.post<IndicatorMeasurement>(
      `${BASE_PATH}/indicators/${indicatorId}/measurements`,
      data
    ),

  // ==========================================================================
  // Certifications
  // ==========================================================================

  createCertification: (data: CertificationCreate) =>
    api.post<Certification>(`${BASE_PATH}/certifications`, data),

  listCertifications: (params?: {
    skip?: number;
    limit?: number;
    status?: CertificationStatus;
    search?: string;
  }) =>
    api.get<CertificationList>(
      `${BASE_PATH}/certifications${buildQueryString(params || {})}`
    ),

  getCertification: (certId: number) =>
    api.get<Certification>(`${BASE_PATH}/certifications/${certId}`),

  updateCertification: (certId: number, data: CertificationUpdate) =>
    api.put<Certification>(`${BASE_PATH}/certifications/${certId}`, data),

  addCertificationAudit: (certId: number, data: CertificationAuditCreate) =>
    api.post<CertificationAudit>(
      `${BASE_PATH}/certifications/${certId}/audits`,
      data
    ),

  updateCertificationAudit: (auditId: number, data: CertificationAuditUpdate) =>
    api.put<CertificationAudit>(
      `${BASE_PATH}/certification-audits/${auditId}`,
      data
    ),

  // ==========================================================================
  // Dashboard
  // ==========================================================================

  getDashboard: () =>
    api.get<QualityDashboard>(`${BASE_PATH}/dashboard`),
};

export default qualityApi;
