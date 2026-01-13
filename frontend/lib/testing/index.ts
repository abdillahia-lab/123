// Enterprise-Grade Testing Utilities
// Mock data generators, test helpers, and fixtures

// ============================================================================
// MOCK DATA GENERATORS
// ============================================================================

let idCounter = 0;

export function generateId(prefix: string = 'test'): string {
  return `${prefix}-${Date.now()}-${++idCounter}`;
}

// Generic mock generator for parcels matching the existing US_PARCELS format
export function generateMockUSParcel(overrides: Record<string, unknown> = {}) {
  const states = ['VA', 'TX', 'CA', 'AZ', 'NV', 'NC', 'FL', 'NY'];
  const counties = ['Loudoun', 'Travis', 'San Diego', 'Maricopa', 'Clark'];
  const viabilities = ['excellent', 'good', 'moderate', 'challenging', 'poor'] as const;
  const permissions = ['By-right', 'Conditional Use', 'Special Exception'] as const;

  const state = states[Math.floor(Math.random() * states.length)];
  const stateIndex = states.indexOf(state);

  return {
    id: generateId('parcel'),
    state,
    county: counties[Math.floor(Math.random() * counties.length)],
    acreage: Math.floor(Math.random() * 500) + 50,
    latitude: 30 + Math.random() * 15,
    longitude: -120 + Math.random() * 40,
    solar_ghi: 4.5 + Math.random() * 2,
    wind_speed_avg: 5 + Math.random() * 5,
    nearest_substation_mi: Math.random() * 20,
    transmission_voltage: [69, 115, 230, 345][Math.floor(Math.random() * 4)],
    solar_capacity_mw: Math.floor(Math.random() * 200) + 20,
    wind_capacity_mw: Math.floor(Math.random() * 100) + 10,
    solar_score: Math.floor(Math.random() * 30) + 70,
    wind_score: Math.floor(Math.random() * 30) + 50,
    grid_score: Math.floor(Math.random() * 30) + 60,
    overall_score: Math.floor(Math.random() * 25) + 70,
    viability: viabilities[Math.floor(Math.random() * 3)],
    solar_permission: permissions[Math.floor(Math.random() * permissions.length)],
    zoning: ['Agricultural', 'Industrial', 'Commercial'][Math.floor(Math.random() * 3)],
    owner_type: ['Private', 'Corporate', 'Government'][Math.floor(Math.random() * 3)],
    land_cost_per_acre: Math.floor(Math.random() * 5000) + 1000,
    utility: ['Dominion Energy', 'PG&E', 'Duke Energy', 'APS'][stateIndex % 4],
    iso_region: ['PJM', 'CAISO', 'ERCOT', 'SPP'][stateIndex % 4],
    energy_community: Math.random() > 0.5,
    disadvantaged_community: Math.random() > 0.7,
    investment_grade: ['A', 'B', 'C'][Math.floor(Math.random() * 3)],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

export function generateMockProject(overrides: Record<string, unknown> = {}) {
  const statuses = [
    'prospecting',
    'site_control',
    'permitting',
    'interconnection',
    'financing',
    'construction',
    'operational',
  ] as const;
  const types = ['solar', 'wind', 'storage', 'hybrid'] as const;

  return {
    id: generateId('project'),
    name: `Solar Farm ${Math.floor(Math.random() * 1000)}`,
    type: types[Math.floor(Math.random() * types.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    parcelIds: [generateId('parcel')],
    capacityMw: Math.floor(Math.random() * 200) + 20,
    estimatedCod: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

export function generateMockUser(overrides: Record<string, unknown> = {}) {
  const roles = ['admin', 'analyst', 'developer', 'viewer'] as const;

  return {
    id: generateId('user'),
    email: `user-${Date.now()}@example.com`,
    name: `Test User ${Math.floor(Math.random() * 100)}`,
    role: roles[Math.floor(Math.random() * roles.length)],
    organization: 'Test Organization',
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

export function generateMockAlert(overrides: Record<string, unknown> = {}) {
  const types = ['info', 'warning', 'success', 'error'] as const;

  return {
    id: generateId('alert'),
    type: types[Math.floor(Math.random() * types.length)],
    title: 'Test Alert',
    message: 'This is a test alert message',
    timestamp: new Date().toISOString(),
    read: false,
    ...overrides,
  };
}

// ============================================================================
// BATCH GENERATORS
// ============================================================================

export function generateMockParcels(count: number) {
  return Array.from({ length: count }, () => generateMockUSParcel());
}

export function generateMockProjects(count: number) {
  return Array.from({ length: count }, () => generateMockProject());
}

// ============================================================================
// TEST HELPERS
// ============================================================================

export function waitFor(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function waitForCondition(
  condition: () => boolean | Promise<boolean>,
  options: { timeout?: number; interval?: number } = {}
): Promise<void> {
  const { timeout = 5000, interval = 100 } = options;
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await waitFor(interval);
  }

  throw new Error(`Condition not met within ${timeout}ms`);
}

export function createMockFetch<T>(response: T, options: { delay?: number; error?: boolean } = {}) {
  const { delay = 0, error = false } = options;

  return async (): Promise<Response> => {
    if (delay > 0) {
      await waitFor(delay);
    }

    if (error) {
      return new Response(JSON.stringify({ error: 'Mock error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };
}

// ============================================================================
// MOCK API HANDLERS
// ============================================================================

export const mockApiHandlers = {
  parcels: {
    list: () => ({
      data: generateMockParcels(25),
      total: 100,
      page: 1,
      limit: 25,
    }),
    get: (id: string) => generateMockUSParcel({ id }),
    search: () => ({
      data: generateMockParcels(10),
      total: 10,
      page: 1,
      limit: 25,
    }),
  },
  projects: {
    list: () => ({
      data: generateMockProjects(10),
      total: 10,
    }),
    get: (id: string) => generateMockProject({ id }),
    create: (data: Record<string, unknown>) => generateMockProject(data),
  },
  stats: () => ({
    parcels_count: 2000,
    total_acreage: 1500000,
    total_capacity_mw: 250000,
    states_count: 50,
  }),
};

// ============================================================================
// ACCESSIBILITY TESTING HELPERS
// ============================================================================

export function checkAriaLabels(element: Element): string[] {
  const issues: string[] = [];

  element.querySelectorAll('img').forEach((img, index) => {
    if (!img.getAttribute('alt')) {
      issues.push(`Image ${index} missing alt attribute`);
    }
  });

  element.querySelectorAll('button').forEach((button, index) => {
    const hasLabel =
      button.textContent?.trim() ||
      button.getAttribute('aria-label') ||
      button.getAttribute('aria-labelledby');
    if (!hasLabel) {
      issues.push(`Button ${index} missing accessible name`);
    }
  });

  element.querySelectorAll('input, select, textarea').forEach((input, index) => {
    const id = input.getAttribute('id');
    const hasLabel =
      input.getAttribute('aria-label') ||
      input.getAttribute('aria-labelledby') ||
      (id && element.querySelector(`label[for="${id}"]`));
    if (!hasLabel && input.getAttribute('type') !== 'hidden') {
      issues.push(`Form input ${index} missing label`);
    }
  });

  element.querySelectorAll('[onclick], [onkeydown]').forEach((el, index) => {
    if (!el.getAttribute('role') && el.tagName.toLowerCase() !== 'button') {
      issues.push(`Interactive element ${index} missing role attribute`);
    }
  });

  return issues;
}

export function checkKeyboardNavigation(element: Element): string[] {
  const issues: string[] = [];
  const focusableSelector =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  const focusableElements = element.querySelectorAll(focusableSelector);

  let prevTabIndex = -1;
  focusableElements.forEach((el, index) => {
    const tabIndex = parseInt(el.getAttribute('tabindex') || '0', 10);
    if (tabIndex > 0 && tabIndex < prevTabIndex) {
      issues.push(`Element ${index} has inconsistent tab order`);
    }
    prevTabIndex = tabIndex > 0 ? tabIndex : prevTabIndex;
  });

  element.querySelectorAll('[tabindex="-1"]').forEach((el, index) => {
    const interactive = el.matches('button, a, input, select, textarea');
    if (interactive) {
      issues.push(`Focusable element ${index} has tabindex=-1 but is interactive`);
    }
  });

  return issues;
}

// ============================================================================
// PERFORMANCE TESTING HELPERS
// ============================================================================

export function measureRenderTime(fn: () => void): number {
  const start = performance.now();
  fn();
  return performance.now() - start;
}

export async function measureAsyncTime(fn: () => Promise<unknown>): Promise<number> {
  const start = performance.now();
  await fn();
  return performance.now() - start;
}

export function createPerformanceObserver(
  callback: (entries: PerformanceEntryList) => void
): PerformanceObserver {
  const observer = new PerformanceObserver((list) => {
    callback(list.getEntries());
  });
  observer.observe({ entryTypes: ['measure', 'mark', 'longtask'] });
  return observer;
}

// ============================================================================
// SNAPSHOT HELPERS
// ============================================================================

export function createSnapshot<T>(data: T): string {
  return JSON.stringify(data, null, 2);
}

export function compareSnapshots(a: string, b: string): boolean {
  return a === b;
}

// ============================================================================
// ERROR INJECTION
// ============================================================================

export function createErrorInjector() {
  let shouldError = false;
  let errorMessage = 'Injected error';

  return {
    enable(message?: string) {
      shouldError = true;
      if (message) errorMessage = message;
    },
    disable() {
      shouldError = false;
    },
    check() {
      if (shouldError) {
        throw new Error(errorMessage);
      }
    },
    wrap<T>(fn: () => T): T {
      this.check();
      return fn();
    },
    async wrapAsync<T>(fn: () => Promise<T>): Promise<T> {
      this.check();
      return fn();
    },
  };
}

// ============================================================================
// TEST DATA CLEANUP
// ============================================================================

const cleanupCallbacks: Array<() => void | Promise<void>> = [];

export function registerCleanup(callback: () => void | Promise<void>): void {
  cleanupCallbacks.push(callback);
}

export async function runCleanup(): Promise<void> {
  for (const callback of cleanupCallbacks) {
    await callback();
  }
  cleanupCallbacks.length = 0;
}
