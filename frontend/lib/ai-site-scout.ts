// AI Site Scout - Natural Language Search and Intelligent Site Analysis
// Parses user queries and finds optimal parcels

import { US_PARCELS, USParcel, searchParcels } from './us-parcels-data';
import { quickParcelValuation } from './financial-model';

export interface SearchQuery {
  // Location filters
  states?: string[];
  counties?: string[];
  excludeStates?: string[];

  // Size filters
  minAcreage?: number;
  maxAcreage?: number;
  minCapacityMW?: number;

  // Score filters
  minOverallScore?: number;
  minSolarScore?: number;
  minWindScore?: number;
  viability?: string[];

  // Resource filters
  minSolarGHI?: number;
  minWindSpeed?: number;

  // Grid filters
  maxSubstationDistance?: number;
  minTransmissionVoltage?: number;

  // Permitting filters
  permissions?: string[];
  zoningTypes?: string[];

  // Owner filters
  ownerTypes?: string[];

  // Financial filters
  maxLandCostPerAcre?: number;
  minInvestmentGrade?: string;

  // Sorting
  sortBy?: 'score' | 'acreage' | 'solar' | 'wind' | 'cost' | 'irr';
  sortOrder?: 'asc' | 'desc';

  // Limit
  limit?: number;
}

export interface SearchResult {
  parcels: EnrichedParcel[];
  totalCount: number;
  query: SearchQuery;
  summary: SearchSummary;
  suggestions: string[];
}

export interface EnrichedParcel extends USParcel {
  rank: number;
  matchScore: number;
  estimatedCapacityMW: number;
  estimatedCapex: number;
  estimatedAnnualRevenue: number;
  estimatedIRR: number;
  investmentGrade: 'A' | 'B' | 'C' | 'D';
  highlights: string[];
}

export interface SearchSummary {
  avgScore: number;
  totalAcreage: number;
  totalCapacityMW: number;
  avgLandCost: number;
  topStates: { state: string; count: number }[];
  scoreDistribution: { range: string; count: number }[];
}

// State name to code mapping
const stateNameToCode: Record<string, string> = {
  'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
  'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
  'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
  'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
  'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
  'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
  'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
  'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
  'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
  'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY',
  // Also support codes directly
  'al': 'AL', 'ak': 'AK', 'az': 'AZ', 'ar': 'AR', 'ca': 'CA', 'co': 'CO', 'ct': 'CT',
  'de': 'DE', 'fl': 'FL', 'ga': 'GA', 'hi': 'HI', 'id': 'ID', 'il': 'IL', 'in': 'IN',
  'ia': 'IA', 'ks': 'KS', 'ky': 'KY', 'la': 'LA', 'me': 'ME', 'md': 'MD', 'ma': 'MA',
  'mi': 'MI', 'mn': 'MN', 'ms': 'MS', 'mo': 'MO', 'mt': 'MT', 'ne': 'NE', 'nv': 'NV',
  'nh': 'NH', 'nj': 'NJ', 'nm': 'NM', 'ny': 'NY', 'nc': 'NC', 'nd': 'ND', 'oh': 'OH',
  'ok': 'OK', 'or': 'OR', 'pa': 'PA', 'ri': 'RI', 'sc': 'SC', 'sd': 'SD', 'tn': 'TN',
  'tx': 'TX', 'ut': 'UT', 'vt': 'VT', 'va': 'VA', 'wa': 'WA', 'wv': 'WV', 'wi': 'WI', 'wy': 'WY'
};

// Parse natural language query into structured search
export function parseNaturalLanguageQuery(query: string): SearchQuery {
  const lowerQuery = query.toLowerCase();
  const searchQuery: SearchQuery = {};

  // Extract states
  const stateMatches: string[] = [];
  for (const [name, code] of Object.entries(stateNameToCode)) {
    if (lowerQuery.includes(name)) {
      if (!stateMatches.includes(code)) {
        stateMatches.push(code);
      }
    }
  }
  if (stateMatches.length > 0) {
    searchQuery.states = stateMatches;
  }

  // Extract acreage requirements
  const acreagePatterns = [
    /(\d+)\+?\s*acres?/i,
    /at least (\d+)\s*acres?/i,
    /minimum (\d+)\s*acres?/i,
    /over (\d+)\s*acres?/i,
    /more than (\d+)\s*acres?/i,
    /(\d+)\s*to\s*(\d+)\s*acres?/i,
    /between (\d+)\s*and\s*(\d+)\s*acres?/i,
  ];

  for (const pattern of acreagePatterns) {
    const match = query.match(pattern);
    if (match) {
      if (match[2]) {
        searchQuery.minAcreage = parseInt(match[1]);
        searchQuery.maxAcreage = parseInt(match[2]);
      } else {
        searchQuery.minAcreage = parseInt(match[1]);
      }
      break;
    }
  }

  // Extract MW capacity requirements
  const mwPatterns = [
    /(\d+)\s*mw/i,
    /(\d+)\s*megawatts?/i,
  ];
  for (const pattern of mwPatterns) {
    const match = query.match(pattern);
    if (match) {
      searchQuery.minCapacityMW = parseInt(match[1]);
      // Convert to acreage (5 acres per MW for solar)
      if (!searchQuery.minAcreage) {
        searchQuery.minAcreage = parseInt(match[1]) * 5;
      }
      break;
    }
  }

  // Extract score requirements
  const scorePatterns = [
    /score\s*(?:of\s*)?(?:at least\s*)?(\d+)/i,
    /(\d+)\+?\s*score/i,
    /minimum\s*score\s*(?:of\s*)?(\d+)/i,
  ];
  for (const pattern of scorePatterns) {
    const match = query.match(pattern);
    if (match) {
      searchQuery.minOverallScore = parseInt(match[1]);
      break;
    }
  }

  // Extract distance requirements
  const distancePatterns = [
    /within (\d+)\s*miles?\s*(?:of\s*)?(?:substation|grid|transmission)/i,
    /(\d+)\s*miles?\s*(?:of\s*)?(?:substation|grid|transmission)/i,
    /close to (?:substation|grid|transmission)/i,
    /near (?:substation|grid|transmission)/i,
  ];
  for (const pattern of distancePatterns) {
    const match = query.match(pattern);
    if (match) {
      if (match[1]) {
        searchQuery.maxSubstationDistance = parseInt(match[1]);
      } else {
        searchQuery.maxSubstationDistance = 5; // Default "close" = 5 miles
      }
      break;
    }
  }

  // Extract transmission voltage requirements
  if (lowerQuery.includes('345kv') || lowerQuery.includes('345 kv')) {
    searchQuery.minTransmissionVoltage = 345;
  } else if (lowerQuery.includes('230kv') || lowerQuery.includes('230 kv')) {
    searchQuery.minTransmissionVoltage = 230;
  } else if (lowerQuery.includes('138kv') || lowerQuery.includes('138 kv')) {
    searchQuery.minTransmissionVoltage = 138;
  } else if (lowerQuery.includes('high voltage') || lowerQuery.includes('high-voltage')) {
    searchQuery.minTransmissionVoltage = 230;
  }

  // Extract permitting requirements
  if (lowerQuery.includes('by-right') || lowerQuery.includes('by right') || lowerQuery.includes('as of right')) {
    searchQuery.permissions = ['By-right'];
  } else if (lowerQuery.includes('conditional')) {
    searchQuery.permissions = ['By-right', 'Conditional Use'];
  }

  // Extract viability requirements
  if (lowerQuery.includes('excellent')) {
    searchQuery.viability = ['excellent'];
  } else if (lowerQuery.includes('good') && !lowerQuery.includes('excellent')) {
    searchQuery.viability = ['excellent', 'good'];
  } else if (lowerQuery.includes('high potential') || lowerQuery.includes('high-potential') || lowerQuery.includes('best')) {
    searchQuery.viability = ['excellent', 'good'];
  }

  // Extract resource type preference
  if (lowerQuery.includes('solar') && !lowerQuery.includes('wind')) {
    searchQuery.sortBy = 'solar';
    if (!searchQuery.minSolarGHI) searchQuery.minSolarGHI = 4.5;
  } else if (lowerQuery.includes('wind') && !lowerQuery.includes('solar')) {
    searchQuery.sortBy = 'wind';
    if (!searchQuery.minWindSpeed) searchQuery.minWindSpeed = 6.5;
  }

  // Extract sorting preferences
  if (lowerQuery.includes('cheapest') || lowerQuery.includes('lowest cost') || lowerQuery.includes('affordable')) {
    searchQuery.sortBy = 'cost';
    searchQuery.sortOrder = 'asc';
  } else if (lowerQuery.includes('largest') || lowerQuery.includes('biggest')) {
    searchQuery.sortBy = 'acreage';
    searchQuery.sortOrder = 'desc';
  } else if (lowerQuery.includes('best') || lowerQuery.includes('top') || lowerQuery.includes('highest')) {
    searchQuery.sortBy = 'score';
    searchQuery.sortOrder = 'desc';
  } else if (lowerQuery.includes('highest irr') || lowerQuery.includes('best returns')) {
    searchQuery.sortBy = 'irr';
    searchQuery.sortOrder = 'desc';
  }

  // Extract limit
  const limitPatterns = [
    /top (\d+)/i,
    /first (\d+)/i,
    /(\d+)\s*(?:parcels?|sites?|results?)/i,
    /show\s*(?:me\s*)?(\d+)/i,
  ];
  for (const pattern of limitPatterns) {
    const match = query.match(pattern);
    if (match) {
      searchQuery.limit = Math.min(parseInt(match[1]), 100);
      break;
    }
  }

  // Default limit if not specified
  if (!searchQuery.limit) {
    searchQuery.limit = 25;
  }

  return searchQuery;
}

// Execute search with enrichment
export function executeSearch(query: SearchQuery): SearchResult {
  let results = [...US_PARCELS];

  // Apply filters
  if (query.states?.length) {
    results = results.filter(p => query.states!.includes(p.state_code));
  }

  if (query.excludeStates?.length) {
    results = results.filter(p => !query.excludeStates!.includes(p.state_code));
  }

  if (query.minAcreage) {
    results = results.filter(p => p.acreage >= query.minAcreage!);
  }

  if (query.maxAcreage) {
    results = results.filter(p => p.acreage <= query.maxAcreage!);
  }

  if (query.minOverallScore) {
    results = results.filter(p => p.overall_score >= query.minOverallScore!);
  }

  if (query.minSolarScore) {
    results = results.filter(p => p.solar_score >= query.minSolarScore!);
  }

  if (query.minWindScore) {
    results = results.filter(p => p.wind_score >= query.minWindScore!);
  }

  if (query.viability?.length) {
    results = results.filter(p => query.viability!.includes(p.viability));
  }

  if (query.minSolarGHI) {
    results = results.filter(p => p.solar_ghi >= query.minSolarGHI!);
  }

  if (query.minWindSpeed) {
    results = results.filter(p => p.wind_speed >= query.minWindSpeed!);
  }

  if (query.maxSubstationDistance) {
    results = results.filter(p => p.nearest_substation_mi <= query.maxSubstationDistance!);
  }

  if (query.minTransmissionVoltage) {
    results = results.filter(p => p.transmission_voltage_kv >= query.minTransmissionVoltage!);
  }

  if (query.permissions?.length) {
    results = results.filter(p => query.permissions!.includes(p.solar_permission));
  }

  if (query.zoningTypes?.length) {
    results = results.filter(p => query.zoningTypes!.includes(p.zoning_type));
  }

  if (query.ownerTypes?.length) {
    results = results.filter(p => query.ownerTypes!.includes(p.owner_type));
  }

  if (query.maxLandCostPerAcre) {
    results = results.filter(p => p.estimated_land_cost_per_acre <= query.maxLandCostPerAcre!);
  }

  const totalCount = results.length;

  // Enrich parcels with financial analysis
  const enrichedParcels: EnrichedParcel[] = results.map(parcel => {
    const valuation = quickParcelValuation({
      acreage: parcel.acreage,
      solar_ghi: parcel.solar_ghi,
      nearest_substation_mi: parcel.nearest_substation_mi,
      estimated_land_cost_per_acre: parcel.estimated_land_cost_per_acre,
    });

    const highlights: string[] = [];
    if (parcel.viability === 'excellent') highlights.push('Excellent viability');
    if (parcel.solar_permission === 'By-right') highlights.push('By-right permitting');
    if (parcel.nearest_substation_mi <= 2) highlights.push('Very close to grid');
    if (parcel.transmission_voltage_kv >= 345) highlights.push('High-voltage transmission');
    if (parcel.solar_ghi >= 5.5) highlights.push('High solar resource');
    if (parcel.wind_speed >= 7.5) highlights.push('Strong wind resource');
    if (valuation.investmentGrade === 'A') highlights.push('Investment grade A');

    return {
      ...parcel,
      rank: 0,
      matchScore: parcel.overall_score,
      ...valuation,
      highlights,
    };
  });

  // Filter by investment grade if specified
  if (query.minInvestmentGrade) {
    const gradeOrder = ['A', 'B', 'C', 'D'];
    const minIndex = gradeOrder.indexOf(query.minInvestmentGrade);
    enrichedParcels.filter(p => gradeOrder.indexOf(p.investmentGrade) <= minIndex);
  }

  // Sort
  const sortBy = query.sortBy || 'score';
  const sortOrder = query.sortOrder || 'desc';

  enrichedParcels.sort((a, b) => {
    let comparison = 0;
    switch (sortBy) {
      case 'score':
        comparison = a.overall_score - b.overall_score;
        break;
      case 'acreage':
        comparison = a.acreage - b.acreage;
        break;
      case 'solar':
        comparison = a.solar_score - b.solar_score;
        break;
      case 'wind':
        comparison = a.wind_score - b.wind_score;
        break;
      case 'cost':
        comparison = a.estimated_land_cost_per_acre - b.estimated_land_cost_per_acre;
        break;
      case 'irr':
        comparison = a.estimatedIRR - b.estimatedIRR;
        break;
    }
    return sortOrder === 'desc' ? -comparison : comparison;
  });

  // Apply limit and add ranks
  const limitedParcels = enrichedParcels.slice(0, query.limit || 25);
  limitedParcels.forEach((p, i) => {
    p.rank = i + 1;
  });

  // Generate summary
  const summary = generateSummary(limitedParcels);

  // Generate suggestions
  const suggestions = generateSuggestions(query, totalCount, limitedParcels);

  return {
    parcels: limitedParcels,
    totalCount,
    query,
    summary,
    suggestions,
  };
}

function generateSummary(parcels: EnrichedParcel[]): SearchSummary {
  if (parcels.length === 0) {
    return {
      avgScore: 0,
      totalAcreage: 0,
      totalCapacityMW: 0,
      avgLandCost: 0,
      topStates: [],
      scoreDistribution: [],
    };
  }

  const avgScore = Math.round(parcels.reduce((sum, p) => sum + p.overall_score, 0) / parcels.length);
  const totalAcreage = parcels.reduce((sum, p) => sum + p.acreage, 0);
  const totalCapacityMW = parcels.reduce((sum, p) => sum + p.estimatedCapacityMW, 0);
  const avgLandCost = Math.round(parcels.reduce((sum, p) => sum + p.estimated_land_cost_per_acre, 0) / parcels.length);

  // Top states
  const stateCounts: Record<string, number> = {};
  for (const p of parcels) {
    stateCounts[p.state_code] = (stateCounts[p.state_code] || 0) + 1;
  }
  const topStates = Object.entries(stateCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([state, count]) => ({ state, count }));

  // Score distribution
  const scoreDistribution = [
    { range: '90-100', count: parcels.filter(p => p.overall_score >= 90).length },
    { range: '80-89', count: parcels.filter(p => p.overall_score >= 80 && p.overall_score < 90).length },
    { range: '70-79', count: parcels.filter(p => p.overall_score >= 70 && p.overall_score < 80).length },
    { range: '60-69', count: parcels.filter(p => p.overall_score >= 60 && p.overall_score < 70).length },
    { range: '<60', count: parcels.filter(p => p.overall_score < 60).length },
  ].filter(d => d.count > 0);

  return {
    avgScore,
    totalAcreage,
    totalCapacityMW,
    avgLandCost,
    topStates,
    scoreDistribution,
  };
}

function generateSuggestions(query: SearchQuery, totalCount: number, results: EnrichedParcel[]): string[] {
  const suggestions: string[] = [];

  if (totalCount === 0) {
    suggestions.push('Try expanding your search criteria');
    if (query.states?.length) {
      suggestions.push('Consider searching in additional states');
    }
    if (query.minAcreage && query.minAcreage > 200) {
      suggestions.push('Try lowering the minimum acreage requirement');
    }
    if (query.minOverallScore && query.minOverallScore > 75) {
      suggestions.push('Try lowering the minimum score threshold');
    }
  } else {
    if (totalCount > 100 && !query.states?.length) {
      suggestions.push('Add state filters to narrow down results');
    }

    const avgScore = results.reduce((sum, p) => sum + p.overall_score, 0) / results.length;
    if (avgScore < 70) {
      suggestions.push('Consider filtering for higher-scoring parcels (score > 75)');
    }

    const byRightCount = results.filter(p => p.solar_permission === 'By-right').length;
    if (byRightCount > 0 && byRightCount < results.length) {
      suggestions.push(`${byRightCount} parcels have by-right permitting - filter for easier development`);
    }

    const gradeACount = results.filter(p => p.investmentGrade === 'A').length;
    if (gradeACount > 0) {
      suggestions.push(`${gradeACount} parcels are investment grade A - prioritize these`);
    }

    if (!query.maxSubstationDistance) {
      const closeToGrid = results.filter(p => p.nearest_substation_mi <= 5).length;
      if (closeToGrid > 0) {
        suggestions.push(`${closeToGrid} parcels are within 5 miles of substations`);
      }
    }
  }

  return suggestions;
}

// Predefined smart searches
export const SMART_SEARCHES = [
  {
    name: 'Best Solar Sites in Texas',
    query: 'Show me the top 25 solar sites in Texas with at least 200 acres and score above 75',
  },
  {
    name: 'Wind Opportunities in the Midwest',
    query: 'Find excellent wind sites in Iowa, Kansas, and Nebraska over 500 acres',
  },
  {
    name: 'By-Right Development Ready',
    query: 'Top 50 parcels with by-right solar permitting and close to transmission lines',
  },
  {
    name: 'High-Voltage Grid Access',
    query: 'Sites within 5 miles of 345kV transmission in California, Arizona, or Nevada',
  },
  {
    name: 'Utility-Scale Opportunities',
    query: 'Parcels over 1000 acres with excellent viability, sorted by highest IRR',
  },
  {
    name: 'Affordable Land Targets',
    query: 'Good or excellent sites with land cost under $3000/acre in the Southeast',
  },
  {
    name: 'Quick Wins',
    query: 'By-right parcels over 100 acres within 2 miles of substation, minimum score 80',
  },
];
