// Core Domain Types - Enterprise-Grade Type Definitions
// Following Domain-Driven Design principles

// ============================================================================
// RESULT PATTERN - For type-safe error handling
// ============================================================================

export type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

export function ok<T>(data: T): Result<T, never> {
  return { success: true, data };
}

export function err<E>(error: E): Result<never, E> {
  return { success: false, error };
}

export function isOk<T, E>(result: Result<T, E>): result is { success: true; data: T } {
  return result.success;
}

export function isErr<T, E>(result: Result<T, E>): result is { success: false; error: E } {
  return !result.success;
}

// ============================================================================
// DOMAIN ERRORS
// ============================================================================

export enum ErrorCode {
  // Client errors (4xx)
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  NOT_FOUND = 'NOT_FOUND',
  CONFLICT = 'CONFLICT',
  RATE_LIMITED = 'RATE_LIMITED',

  // Server errors (5xx)
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  EXTERNAL_SERVICE_ERROR = 'EXTERNAL_SERVICE_ERROR',

  // Domain errors
  INVALID_PARCEL = 'INVALID_PARCEL',
  ANALYSIS_FAILED = 'ANALYSIS_FAILED',
  EXPORT_FAILED = 'EXPORT_FAILED',
}

export interface DomainError {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
  stack?: string;
  timestamp: string;
  requestId?: string;
}

export function createError(
  code: ErrorCode,
  message: string,
  details?: Record<string, unknown>
): DomainError {
  return {
    code,
    message,
    details,
    timestamp: new Date().toISOString(),
  };
}

// ============================================================================
// PAGINATION
// ============================================================================

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    totalCount: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  meta?: {
    requestId: string;
    timestamp: string;
    processingTimeMs: number;
  };
}

// ============================================================================
// API RESPONSE WRAPPER
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: DomainError;
  meta: {
    requestId: string;
    timestamp: string;
    version: string;
  };
}

// ============================================================================
// ENTITY BASE TYPES
// ============================================================================

export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export interface AuditableEntity extends BaseEntity {
  createdBy?: string;
  updatedBy?: string;
  deletedAt?: string;
  deletedBy?: string;
}

// ============================================================================
// PARCEL DOMAIN TYPES
// ============================================================================

export type Viability = 'excellent' | 'good' | 'moderate' | 'challenging' | 'poor';
export type SolarPermission = 'By-right' | 'Conditional Use' | 'Special Exception' | 'Prohibited';
export type OwnerType = 'Private' | 'Corporate' | 'Government' | 'Trust';
export type InvestmentGrade = 'A' | 'B' | 'C' | 'D' | 'F';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface SolarMetrics {
  ghi: number; // Global Horizontal Irradiance (kWh/m²/day)
  dni: number; // Direct Normal Irradiance (kWh/m²/day)
  score: number;
  capacityMw: number;
}

export interface WindMetrics {
  speed: number; // m/s at hub height
  score: number;
  capacityMw: number;
}

export interface GridConnection {
  nearestSubstationMi: number;
  transmissionVoltageKv: number;
  score: number;
}

export interface FinancialEstimates {
  landCostPerAcre: number;
  developmentCost: number;
  estimatedCapex: number;
  estimatedAnnualRevenue: number;
  estimatedIrr: number;
  investmentGrade: InvestmentGrade;
}

export interface ParcelScores {
  overall: number;
  solar: number;
  wind: number;
  grid: number;
  permitting: number;
  environmental: number;
  land: number;
}

export interface Parcel extends AuditableEntity {
  // Identification
  apn: string;
  address: string;

  // Location
  state: string;
  stateCode: string;
  county: string;
  municipality: string;
  coordinates: Coordinates;

  // Physical
  acreage: number;
  zoningType: string;
  landUse: string;

  // Ownership
  ownerName: string;
  ownerType: OwnerType;

  // Permitting
  solarPermission: SolarPermission;

  // Resources
  solar: SolarMetrics;
  wind: WindMetrics;
  grid: GridConnection;

  // Scores
  scores: ParcelScores;
  viability: Viability;

  // Financial
  financial: FinancialEstimates;
}

// ============================================================================
// PROJECT DOMAIN TYPES
// ============================================================================

export type ProjectStatus =
  | 'prospecting'
  | 'site_control'
  | 'permitting'
  | 'interconnection'
  | 'financing'
  | 'construction'
  | 'operational'
  | 'decommissioned';

export type ProjectType = 'solar' | 'wind' | 'storage' | 'hybrid';

export interface ProjectMilestone {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  dueDate?: string;
  completedDate?: string;
  notes?: string;
}

export interface Project extends AuditableEntity {
  name: string;
  type: ProjectType;
  status: ProjectStatus;
  parcelIds: string[];
  capacityMw: number;
  estimatedCod: string;
  milestones: ProjectMilestone[];
  documents: ProjectDocument[];
  financials?: ProjectFinancials;
}

export interface ProjectDocument {
  id: string;
  name: string;
  type: string;
  url: string;
  uploadedAt: string;
  uploadedBy: string;
}

export interface ProjectFinancials {
  totalCapex: number;
  debtAmount: number;
  equityAmount: number;
  projectedIrr: number;
  projectedNpv: number;
  ppaRate?: number;
  ppaTermYears?: number;
}

// ============================================================================
// USER & AUTH TYPES
// ============================================================================

export type UserRole = 'admin' | 'analyst' | 'developer' | 'viewer';

export interface User extends BaseEntity {
  email: string;
  name: string;
  role: UserRole;
  organization?: string;
  avatar?: string;
  preferences: UserPreferences;
  lastLoginAt?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    alerts: boolean;
  };
  defaultView: 'dashboard' | 'scout' | 'map';
  favoriteStates: string[];
}

export interface AuthSession {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
}

// ============================================================================
// SEARCH & FILTER TYPES
// ============================================================================

export interface ParcelSearchQuery {
  // Location
  states?: string[];
  counties?: string[];
  excludeStates?: string[];

  // Size
  minAcreage?: number;
  maxAcreage?: number;
  minCapacityMw?: number;

  // Scores
  minOverallScore?: number;
  minSolarScore?: number;
  minWindScore?: number;
  viability?: Viability[];

  // Resources
  minSolarGhi?: number;
  minWindSpeed?: number;

  // Grid
  maxSubstationDistance?: number;
  minTransmissionVoltage?: number;

  // Permitting
  permissions?: SolarPermission[];
  zoningTypes?: string[];

  // Financial
  maxLandCostPerAcre?: number;
  minInvestmentGrade?: InvestmentGrade;

  // Text
  searchText?: string;

  // Pagination
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface SearchResult<T> {
  items: T[];
  totalCount: number;
  query: ParcelSearchQuery;
  summary: SearchSummary;
  suggestions: string[];
  facets?: SearchFacets;
}

export interface SearchSummary {
  avgScore: number;
  totalAcreage: number;
  totalCapacityMw: number;
  avgLandCost: number;
  topStates: Array<{ state: string; count: number }>;
  scoreDistribution: Array<{ range: string; count: number }>;
}

export interface SearchFacets {
  states: Array<{ value: string; count: number }>;
  viability: Array<{ value: Viability; count: number }>;
  permissions: Array<{ value: SolarPermission; count: number }>;
  zoningTypes: Array<{ value: string; count: number }>;
}

// ============================================================================
// ANALYTICS & REPORTING
// ============================================================================

export interface AnalyticsEvent {
  eventType: string;
  userId?: string;
  sessionId: string;
  timestamp: string;
  properties: Record<string, unknown>;
}

export interface ReportConfig {
  type: 'parcel_analysis' | 'financial_model' | 'market_report' | 'portfolio_summary';
  parcelIds?: string[];
  projectIds?: string[];
  dateRange?: { start: string; end: string };
  format: 'pdf' | 'xlsx' | 'csv' | 'json';
  includeCharts?: boolean;
  customFields?: string[];
}

// ============================================================================
// NOTIFICATIONS & ALERTS
// ============================================================================

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';

export interface Alert {
  id: string;
  type: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  source: string;
  timestamp: string;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  resolvedAt?: string;
  resolvedBy?: string;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// WEBHOOK & INTEGRATION TYPES
// ============================================================================

export type WebhookEvent =
  | 'parcel.created'
  | 'parcel.updated'
  | 'parcel.analyzed'
  | 'project.created'
  | 'project.status_changed'
  | 'alert.triggered'
  | 'report.generated';

export interface WebhookConfig {
  id: string;
  url: string;
  events: WebhookEvent[];
  secret: string;
  active: boolean;
  createdAt: string;
  lastTriggeredAt?: string;
  failureCount: number;
}

export interface WebhookPayload<T = unknown> {
  id: string;
  event: WebhookEvent;
  timestamp: string;
  data: T;
  signature: string;
}
