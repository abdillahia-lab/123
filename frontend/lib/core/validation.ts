// Enterprise-Grade Input Validation
// Using Zod for runtime type checking and validation

import { z } from 'zod';

// ============================================================================
// COMMON VALIDATORS
// ============================================================================

export const coordinatesSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
});

export const paginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});

export const dateRangeSchema = z.object({
  start: z.string().datetime(),
  end: z.string().datetime(),
}).refine(data => new Date(data.start) <= new Date(data.end), {
  message: 'Start date must be before or equal to end date',
});

// ============================================================================
// PARCEL VALIDATORS
// ============================================================================

export const stateCodeSchema = z.string().length(2).toUpperCase();

export const viabilitySchema = z.enum(['excellent', 'good', 'moderate', 'challenging', 'poor']);

export const solarPermissionSchema = z.enum(['By-right', 'Conditional Use', 'Special Exception', 'Prohibited']);

export const ownerTypeSchema = z.enum(['Private', 'Corporate', 'Government', 'Trust']);

export const investmentGradeSchema = z.enum(['A', 'B', 'C', 'D', 'F']);

export const parcelSearchSchema = z.object({
  // Location filters
  states: z.array(stateCodeSchema).optional(),
  counties: z.array(z.string().min(1).max(100)).optional(),
  excludeStates: z.array(stateCodeSchema).optional(),

  // Size filters
  minAcreage: z.coerce.number().min(0).optional(),
  maxAcreage: z.coerce.number().min(0).optional(),
  minCapacityMw: z.coerce.number().min(0).optional(),

  // Score filters
  minOverallScore: z.coerce.number().min(0).max(100).optional(),
  minSolarScore: z.coerce.number().min(0).max(100).optional(),
  minWindScore: z.coerce.number().min(0).max(100).optional(),
  viability: z.array(viabilitySchema).optional(),

  // Resource filters
  minSolarGhi: z.coerce.number().min(0).max(10).optional(),
  minWindSpeed: z.coerce.number().min(0).max(20).optional(),

  // Grid filters
  maxSubstationDistance: z.coerce.number().min(0).optional(),
  minTransmissionVoltage: z.coerce.number().min(0).optional(),

  // Permitting filters
  permissions: z.array(solarPermissionSchema).optional(),
  zoningTypes: z.array(z.string()).optional(),

  // Financial filters
  maxLandCostPerAcre: z.coerce.number().min(0).optional(),
  minInvestmentGrade: investmentGradeSchema.optional(),

  // Text search
  searchText: z.string().max(500).optional(),

  // Pagination
  ...paginationSchema.shape,
}).refine(data => {
  if (data.minAcreage && data.maxAcreage) {
    return data.minAcreage <= data.maxAcreage;
  }
  return true;
}, {
  message: 'minAcreage must be less than or equal to maxAcreage',
});

export const parcelIdSchema = z.string()
  .min(1)
  .max(100)
  .regex(/^[a-z]{2}-\d{4}$/, 'Invalid parcel ID format');

// ============================================================================
// PROJECT VALIDATORS
// ============================================================================

export const projectStatusSchema = z.enum([
  'prospecting',
  'site_control',
  'permitting',
  'interconnection',
  'financing',
  'construction',
  'operational',
  'decommissioned',
]);

export const projectTypeSchema = z.enum(['solar', 'wind', 'storage', 'hybrid']);

export const createProjectSchema = z.object({
  name: z.string().min(1).max(200),
  type: projectTypeSchema,
  parcelIds: z.array(parcelIdSchema).min(1),
  capacityMw: z.number().positive(),
  estimatedCod: z.string().datetime().optional(),
  notes: z.string().max(5000).optional(),
});

export const updateProjectSchema = createProjectSchema.partial();

// ============================================================================
// FINANCIAL MODEL VALIDATORS
// ============================================================================

export const financialAssumptionsSchema = z.object({
  // Project parameters
  capacityMw: z.number().positive().max(10000),
  capacityFactorPct: z.number().min(10).max(60),
  projectLifeYears: z.number().int().min(10).max(50),
  degradationPctPerYear: z.number().min(0).max(2),

  // Capital costs
  capexPerWatt: z.number().min(0.1).max(5),
  interconnectionCost: z.number().min(0),
  landCostTotal: z.number().min(0),
  developmentCost: z.number().min(0),

  // Operating costs
  opexPerKwYear: z.number().min(0).max(50),
  opexEscalationPct: z.number().min(0).max(10),

  // Revenue
  ppaRatePerMwh: z.number().min(0).max(200),
  ppaEscalationPct: z.number().min(-5).max(10),

  // Financing
  debtPct: z.number().min(0).max(100),
  debtInterestRate: z.number().min(0).max(20),
  debtTermYears: z.number().int().min(0).max(30),

  // Tax
  itcPct: z.number().min(0).max(70),
  ptcPerMwh: z.number().min(0).max(50),
  usePTC: z.boolean(),

  // Adders
  domesticContentBonus: z.boolean(),
  energyCommunityBonus: z.boolean(),
  lowIncomeBonus: z.boolean(),
});

// ============================================================================
// USER VALIDATORS
// ============================================================================

export const emailSchema = z.string().email().max(255);

export const passwordSchema = z.string()
  .min(12, 'Password must be at least 12 characters')
  .max(128)
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character');

export const userRoleSchema = z.enum(['admin', 'analyst', 'developer', 'viewer']);

export const userPreferencesSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']),
  notifications: z.object({
    email: z.boolean(),
    push: z.boolean(),
    alerts: z.boolean(),
  }),
  defaultView: z.enum(['dashboard', 'scout', 'map']),
  favoriteStates: z.array(stateCodeSchema).max(50),
});

export const createUserSchema = z.object({
  email: emailSchema,
  name: z.string().min(1).max(200),
  role: userRoleSchema,
  organization: z.string().max(200).optional(),
});

// ============================================================================
// WEBHOOK VALIDATORS
// ============================================================================

export const webhookEventSchema = z.enum([
  'parcel.created',
  'parcel.updated',
  'parcel.analyzed',
  'project.created',
  'project.status_changed',
  'alert.triggered',
  'report.generated',
]);

export const createWebhookSchema = z.object({
  url: z.string().url().max(2048),
  events: z.array(webhookEventSchema).min(1),
  secret: z.string().min(32).max(128).optional(),
});

// ============================================================================
// REPORT VALIDATORS
// ============================================================================

export const reportFormatSchema = z.enum(['pdf', 'xlsx', 'csv', 'json']);

export const reportConfigSchema = z.object({
  type: z.enum(['parcel_analysis', 'financial_model', 'market_report', 'portfolio_summary']),
  parcelIds: z.array(parcelIdSchema).optional(),
  projectIds: z.array(z.string()).optional(),
  dateRange: dateRangeSchema.optional(),
  format: reportFormatSchema,
  includeCharts: z.boolean().default(true),
  customFields: z.array(z.string()).max(50).optional(),
});

// ============================================================================
// VALIDATION UTILITIES
// ============================================================================

export type ValidationResult<T> =
  | { success: true; data: T }
  | { success: false; errors: ValidationError[] };

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export function validate<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): ValidationResult<T> {
  const result = schema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  const errors: ValidationError[] = result.error.issues.map(err => ({
    field: err.path.join('.'),
    message: err.message,
    code: err.code,
  }));

  return { success: false, errors };
}

export function validateOrThrow<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

// ============================================================================
// SANITIZATION UTILITIES
// ============================================================================

export function sanitizeString(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .slice(0, 10000); // Limit length
}

export function sanitizeSearchQuery(query: string): string {
  return query
    .trim()
    .toLowerCase()
    .replace(/[^\w\s\-.,]/g, '') // Only allow alphanumeric, spaces, and basic punctuation
    .slice(0, 500);
}

export function sanitizeHtml(input: string): string {
  const htmlEntities: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  };

  return input.replace(/[&<>"'/]/g, char => htmlEntities[char] || char);
}
