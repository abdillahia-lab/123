// Parcel Alert Subscription System
// Real-time notifications for new parcels matching criteria

import type { Result } from '../core/types';

// ============================================================================
// TYPES
// ============================================================================

export interface AlertCriteria {
  // Location filters
  states?: string[];
  counties?: string[];
  excludeStates?: string[];

  // Size filters
  minAcreage?: number;
  maxAcreage?: number;

  // Score filters
  minOverallScore?: number;
  minSolarScore?: number;
  minWindScore?: number;
  viability?: ('excellent' | 'good' | 'moderate')[];

  // Grid filters
  maxSubstationDistance?: number;
  minTransmissionVoltage?: number;
  isoRegions?: string[];

  // Permitting
  permissions?: ('By-right' | 'Conditional Use' | 'Special Exception')[];
  zoningTypes?: string[];

  // Financial
  maxLandCostPerAcre?: number;
  minCapacityMw?: number;

  // Special designations
  energyCommunity?: boolean;
  disadvantagedCommunity?: boolean;
}

export interface AlertSubscription {
  id: string;
  userId: string;
  name: string;
  criteria: AlertCriteria;
  channels: {
    email: boolean;
    push: boolean;
    inApp: boolean;
    webhook?: string;
  };
  frequency: 'instant' | 'hourly' | 'daily' | 'weekly';
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  lastTriggered?: string;
  matchCount: number;
}

export interface AlertMatch {
  id: string;
  subscriptionId: string;
  parcelId: string;
  matchedAt: string;
  matchScore: number;
  matchedCriteria: string[];
  notificationSent: boolean;
  parcelData: {
    state: string;
    county: string;
    acreage: number;
    overallScore: number;
    solarCapacityMw: number;
    viability: string;
  };
}

export interface AlertDigest {
  subscriptionId: string;
  subscriptionName: string;
  period: { start: string; end: string };
  newMatches: number;
  topMatches: AlertMatch[];
  summaryStats: {
    avgScore: number;
    totalAcreage: number;
    totalCapacity: number;
    stateBreakdown: Record<string, number>;
  };
}

// ============================================================================
// ALERT SUBSCRIPTION STORE (In production, this would be a database)
// ============================================================================

const subscriptions = new Map<string, AlertSubscription>();
const matches = new Map<string, AlertMatch[]>();

// ============================================================================
// ALERT SERVICE
// ============================================================================

export const alertService = {
  // Create a new alert subscription
  async createSubscription(
    userId: string,
    name: string,
    criteria: AlertCriteria,
    channels: AlertSubscription['channels'],
    frequency: AlertSubscription['frequency'] = 'daily'
  ): Promise<Result<AlertSubscription, Error>> {
    try {
      const id = `alert-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const subscription: AlertSubscription = {
        id,
        userId,
        name,
        criteria,
        channels,
        frequency,
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        matchCount: 0,
      };

      subscriptions.set(id, subscription);

      // Run initial match check
      const initialMatches = await this.checkForMatches(subscription);

      return { success: true, data: { ...subscription, matchCount: initialMatches.length } };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error : new Error('Failed to create subscription') };
    }
  },

  // Update subscription
  async updateSubscription(
    id: string,
    updates: Partial<Pick<AlertSubscription, 'name' | 'criteria' | 'channels' | 'frequency' | 'isActive'>>
  ): Promise<Result<AlertSubscription, Error>> {
    const subscription = subscriptions.get(id);
    if (!subscription) {
      return { success: false, error: new Error('Subscription not found') };
    }

    const updated = {
      ...subscription,
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    subscriptions.set(id, updated);
    return { success: true, data: updated };
  },

  // Delete subscription
  async deleteSubscription(id: string): Promise<Result<void, Error>> {
    if (!subscriptions.has(id)) {
      return { success: false, error: new Error('Subscription not found') };
    }

    subscriptions.delete(id);
    matches.delete(id);
    return { success: true, data: undefined };
  },

  // Get user's subscriptions
  async getUserSubscriptions(userId: string): Promise<Result<AlertSubscription[], Error>> {
    const userSubs = Array.from(subscriptions.values()).filter(s => s.userId === userId);
    return { success: true, data: userSubs };
  },

  // Get subscription matches
  async getSubscriptionMatches(subscriptionId: string, limit: number = 50): Promise<Result<AlertMatch[], Error>> {
    const subMatches = matches.get(subscriptionId) || [];
    return { success: true, data: subMatches.slice(0, limit) };
  },

  // Check parcels against a subscription's criteria
  async checkForMatches(subscription: AlertSubscription, parcels?: ParcelData[]): Promise<AlertMatch[]> {
    // In production, this would query the database
    // For demo, use mock data
    const testParcels = parcels || generateMockNewParcels(10);
    const newMatches: AlertMatch[] = [];

    for (const parcel of testParcels) {
      const matchResult = this.evaluateParcel(parcel, subscription.criteria);

      if (matchResult.matches) {
        const match: AlertMatch = {
          id: `match-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          subscriptionId: subscription.id,
          parcelId: parcel.id,
          matchedAt: new Date().toISOString(),
          matchScore: matchResult.score,
          matchedCriteria: matchResult.matchedCriteria,
          notificationSent: false,
          parcelData: {
            state: parcel.state,
            county: parcel.county,
            acreage: parcel.acreage,
            overallScore: parcel.overall_score,
            solarCapacityMw: parcel.solar_capacity_mw,
            viability: parcel.viability,
          },
        };

        newMatches.push(match);
      }
    }

    // Store matches
    const existingMatches = matches.get(subscription.id) || [];
    matches.set(subscription.id, [...newMatches, ...existingMatches].slice(0, 500));

    // Update subscription match count
    const sub = subscriptions.get(subscription.id);
    if (sub) {
      sub.matchCount += newMatches.length;
      sub.lastTriggered = new Date().toISOString();
      subscriptions.set(subscription.id, sub);
    }

    return newMatches;
  },

  // Evaluate a single parcel against criteria
  evaluateParcel(
    parcel: ParcelData,
    criteria: AlertCriteria
  ): { matches: boolean; score: number; matchedCriteria: string[] } {
    const matchedCriteria: string[] = [];
    let score = 0;
    let requiredMatches = 0;
    let totalMatches = 0;

    // State filter
    if (criteria.states?.length) {
      requiredMatches++;
      if (criteria.states.includes(parcel.state_code || parcel.state)) {
        totalMatches++;
        matchedCriteria.push(`State: ${parcel.state}`);
        score += 10;
      }
    }

    // Exclude states
    if (criteria.excludeStates?.length) {
      if (criteria.excludeStates.includes(parcel.state_code || parcel.state)) {
        return { matches: false, score: 0, matchedCriteria: [] };
      }
    }

    // Acreage
    if (criteria.minAcreage !== undefined) {
      requiredMatches++;
      if (parcel.acreage >= criteria.minAcreage) {
        totalMatches++;
        matchedCriteria.push(`Acreage: ${parcel.acreage} >= ${criteria.minAcreage}`);
        score += 15;
      }
    }

    if (criteria.maxAcreage !== undefined) {
      requiredMatches++;
      if (parcel.acreage <= criteria.maxAcreage) {
        totalMatches++;
        matchedCriteria.push(`Acreage: ${parcel.acreage} <= ${criteria.maxAcreage}`);
        score += 5;
      }
    }

    // Overall score
    if (criteria.minOverallScore !== undefined) {
      requiredMatches++;
      if (parcel.overall_score >= criteria.minOverallScore) {
        totalMatches++;
        matchedCriteria.push(`Score: ${parcel.overall_score} >= ${criteria.minOverallScore}`);
        score += 20;
      }
    }

    // Solar score
    if (criteria.minSolarScore !== undefined) {
      requiredMatches++;
      if (parcel.solar_score >= criteria.minSolarScore) {
        totalMatches++;
        matchedCriteria.push(`Solar Score: ${parcel.solar_score}`);
        score += 15;
      }
    }

    // Wind score
    if (criteria.minWindScore !== undefined) {
      requiredMatches++;
      if (parcel.wind_score >= criteria.minWindScore) {
        totalMatches++;
        matchedCriteria.push(`Wind Score: ${parcel.wind_score}`);
        score += 15;
      }
    }

    // Viability
    if (criteria.viability?.length) {
      requiredMatches++;
      if (criteria.viability.includes(parcel.viability as 'excellent' | 'good' | 'moderate')) {
        totalMatches++;
        matchedCriteria.push(`Viability: ${parcel.viability}`);
        score += 20;
      }
    }

    // Substation distance
    if (criteria.maxSubstationDistance !== undefined) {
      requiredMatches++;
      if (parcel.nearest_substation_mi <= criteria.maxSubstationDistance) {
        totalMatches++;
        matchedCriteria.push(`Substation: ${parcel.nearest_substation_mi} mi`);
        score += 15;
      }
    }

    // Transmission voltage
    if (criteria.minTransmissionVoltage !== undefined) {
      requiredMatches++;
      if (parcel.transmission_voltage_kv >= criteria.minTransmissionVoltage) {
        totalMatches++;
        matchedCriteria.push(`Transmission: ${parcel.transmission_voltage_kv} kV`);
        score += 10;
      }
    }

    // Permitting
    if (criteria.permissions?.length) {
      requiredMatches++;
      if (criteria.permissions.includes(parcel.solar_permission as 'By-right' | 'Conditional Use' | 'Special Exception')) {
        totalMatches++;
        matchedCriteria.push(`Permission: ${parcel.solar_permission}`);
        score += 25;
      }
    }

    // Land cost
    if (criteria.maxLandCostPerAcre !== undefined) {
      requiredMatches++;
      if (parcel.estimated_land_cost_per_acre <= criteria.maxLandCostPerAcre) {
        totalMatches++;
        matchedCriteria.push(`Land Cost: $${parcel.estimated_land_cost_per_acre}/acre`);
        score += 15;
      }
    }

    // Capacity
    if (criteria.minCapacityMw !== undefined) {
      requiredMatches++;
      if (parcel.solar_capacity_mw >= criteria.minCapacityMw) {
        totalMatches++;
        matchedCriteria.push(`Capacity: ${parcel.solar_capacity_mw} MW`);
        score += 15;
      }
    }

    // Energy community
    if (criteria.energyCommunity !== undefined && criteria.energyCommunity) {
      requiredMatches++;
      if (parcel.energy_community) {
        totalMatches++;
        matchedCriteria.push('Energy Community');
        score += 20;
      }
    }

    // Disadvantaged community
    if (criteria.disadvantagedCommunity !== undefined && criteria.disadvantagedCommunity) {
      requiredMatches++;
      if (parcel.disadvantaged_community) {
        totalMatches++;
        matchedCriteria.push('Disadvantaged Community');
        score += 15;
      }
    }

    // A parcel matches if it meets ALL required criteria
    const matches = requiredMatches === 0 || totalMatches === requiredMatches;

    return { matches, score, matchedCriteria };
  },

  // Generate digest for a subscription
  async generateDigest(subscriptionId: string, periodDays: number = 7): Promise<Result<AlertDigest, Error>> {
    const subscription = subscriptions.get(subscriptionId);
    if (!subscription) {
      return { success: false, error: new Error('Subscription not found') };
    }

    const subMatches = matches.get(subscriptionId) || [];
    const periodStart = new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000);

    const recentMatches = subMatches.filter(m => new Date(m.matchedAt) >= periodStart);
    const stateBreakdown: Record<string, number> = {};
    let totalAcreage = 0;
    let totalCapacity = 0;
    let totalScore = 0;

    recentMatches.forEach(match => {
      stateBreakdown[match.parcelData.state] = (stateBreakdown[match.parcelData.state] || 0) + 1;
      totalAcreage += match.parcelData.acreage;
      totalCapacity += match.parcelData.solarCapacityMw;
      totalScore += match.parcelData.overallScore;
    });

    return {
      success: true,
      data: {
        subscriptionId,
        subscriptionName: subscription.name,
        period: {
          start: periodStart.toISOString(),
          end: new Date().toISOString(),
        },
        newMatches: recentMatches.length,
        topMatches: recentMatches.sort((a, b) => b.matchScore - a.matchScore).slice(0, 10),
        summaryStats: {
          avgScore: recentMatches.length > 0 ? totalScore / recentMatches.length : 0,
          totalAcreage,
          totalCapacity,
          stateBreakdown,
        },
      },
    };
  },
};

// ============================================================================
// PARCEL DATA TYPE (for matching)
// ============================================================================

interface ParcelData {
  id: string;
  state: string;
  state_code?: string;
  county: string;
  acreage: number;
  overall_score: number;
  solar_score: number;
  wind_score: number;
  viability: string;
  solar_permission: string;
  nearest_substation_mi: number;
  transmission_voltage_kv: number;
  solar_capacity_mw: number;
  wind_capacity_mw: number;
  estimated_land_cost_per_acre: number;
  energy_community?: boolean;
  disadvantaged_community?: boolean;
}

// ============================================================================
// MOCK NEW PARCELS (Simulates new parcels coming to market)
// ============================================================================

function generateMockNewParcels(count: number): ParcelData[] {
  const states = [
    { code: 'TX', name: 'Texas' },
    { code: 'CA', name: 'California' },
    { code: 'AZ', name: 'Arizona' },
    { code: 'NV', name: 'Nevada' },
    { code: 'FL', name: 'Florida' },
    { code: 'NC', name: 'North Carolina' },
    { code: 'VA', name: 'Virginia' },
    { code: 'OH', name: 'Ohio' },
  ];

  const counties = ['Solar', 'Wind', 'Energy', 'Green', 'Power'];
  const viabilities = ['excellent', 'good', 'moderate', 'challenging'];
  const permissions = ['By-right', 'Conditional Use', 'Special Exception'];

  return Array.from({ length: count }, (_, i) => {
    const state = states[Math.floor(Math.random() * states.length)];
    return {
      id: `new-${Date.now()}-${i}`,
      state: state.name,
      state_code: state.code,
      county: `${counties[Math.floor(Math.random() * counties.length)]} County`,
      acreage: 100 + Math.floor(Math.random() * 900),
      overall_score: 60 + Math.floor(Math.random() * 40),
      solar_score: 60 + Math.floor(Math.random() * 40),
      wind_score: 40 + Math.floor(Math.random() * 50),
      viability: viabilities[Math.floor(Math.random() * viabilities.length)],
      solar_permission: permissions[Math.floor(Math.random() * permissions.length)],
      nearest_substation_mi: 0.5 + Math.random() * 10,
      transmission_voltage_kv: [69, 115, 138, 230, 345, 500][Math.floor(Math.random() * 6)],
      solar_capacity_mw: 20 + Math.floor(Math.random() * 180),
      wind_capacity_mw: 5 + Math.floor(Math.random() * 45),
      estimated_land_cost_per_acre: 1000 + Math.floor(Math.random() * 9000),
      energy_community: Math.random() > 0.7,
      disadvantaged_community: Math.random() > 0.8,
    };
  });
}

// ============================================================================
// PRESET ALERT TEMPLATES
// ============================================================================

export const alertTemplates: Record<string, { name: string; criteria: AlertCriteria }> = {
  texasSolar: {
    name: 'Premium Texas Solar Sites',
    criteria: {
      states: ['TX'],
      minAcreage: 200,
      minOverallScore: 80,
      permissions: ['By-right'],
      viability: ['excellent', 'good'],
    },
  },
  midwestWind: {
    name: 'Midwest Wind Opportunities',
    criteria: {
      states: ['IA', 'KS', 'NE', 'OK', 'MN'],
      minAcreage: 500,
      minWindScore: 75,
      viability: ['excellent', 'good'],
    },
  },
  gridReady: {
    name: 'Grid-Ready Development Sites',
    criteria: {
      maxSubstationDistance: 3,
      minTransmissionVoltage: 230,
      permissions: ['By-right'],
      minOverallScore: 75,
    },
  },
  valueBuys: {
    name: 'Value Investment Targets',
    criteria: {
      maxLandCostPerAcre: 3000,
      minOverallScore: 70,
      minCapacityMw: 50,
      viability: ['excellent', 'good', 'moderate'],
    },
  },
  iraBonus: {
    name: 'IRA Bonus-Eligible Sites',
    criteria: {
      energyCommunity: true,
      minOverallScore: 70,
      minAcreage: 100,
    },
  },
  utilityScale: {
    name: 'Utility-Scale Opportunities',
    criteria: {
      minAcreage: 500,
      minCapacityMw: 100,
      minOverallScore: 80,
      viability: ['excellent'],
    },
  },
};
