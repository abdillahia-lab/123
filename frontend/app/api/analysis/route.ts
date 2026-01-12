import { NextResponse } from 'next/server';
import { getParcelById } from '@/lib/us-parcels-data';

// Simulate analysis delay for realistic UX
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function POST(request: Request) {
  const body = await request.json();
  const { parcel_id, project_type = 'utility_solar' } = body;

  // Simulate analysis processing time
  await delay(800);

  // Try to get real parcel data
  const parcel = getParcelById(parcel_id);

  if (parcel) {
    // Use actual parcel data for analysis
    const permittingScore = calculatePermittingScore(parcel);
    const gridScore = calculateGridScore(parcel);
    const envScore = calculateEnvironmentalScore(parcel);
    const landScore = calculateLandScore(parcel);
    const financialScore = calculateFinancialScore(parcel);

    // Weighted overall score (matches architecture doc)
    const overallScore =
      permittingScore * 0.25 +
      gridScore * 0.30 +
      envScore * 0.20 +
      landScore * 0.15 +
      financialScore * 0.10;

    let viability: string;
    if (overallScore >= 85) viability = 'excellent';
    else if (overallScore >= 70) viability = 'good';
    else if (overallScore >= 55) viability = 'moderate';
    else if (overallScore >= 40) viability = 'challenging';
    else viability = 'poor';

    // Generate contextual recommendations
    const recommendations = generateRecommendations(parcel, {
      permittingScore,
      gridScore,
      envScore,
      landScore,
      financialScore
    });

    // Identify fatal flaws
    const fatal_flaws = identifyFatalFlaws(parcel, {
      permittingScore,
      gridScore,
      envScore,
      landScore
    });

    return NextResponse.json({
      id: `analysis-${Date.now()}`,
      parcel_id,
      project_type,
      status: 'completed',
      overall_score: Math.round(overallScore * 10) / 10,
      permitting_score: Math.round(permittingScore),
      grid_score: Math.round(gridScore),
      environmental_score: Math.round(envScore),
      land_score: Math.round(landScore),
      financial_score: Math.round(financialScore),
      viability,
      fatal_flaws,
      recommendations,
      // Additional insights
      insights: {
        solar_potential: {
          ghi: parcel.solar_ghi,
          capacity_mw: parcel.solar_capacity_mw,
          annual_mwh: Math.round(parcel.solar_capacity_mw * parcel.solar_ghi * 365 * 0.2),
          lcoe_estimate: Math.round((25 + (100 - overallScore) * 0.3) * 10) / 10
        },
        wind_potential: {
          speed_ms: parcel.wind_speed,
          capacity_mw: parcel.wind_capacity_mw,
          annual_mwh: Math.round(parcel.wind_capacity_mw * parcel.wind_speed * 365 * 0.35)
        },
        financial: {
          land_cost: parcel.acreage * parcel.estimated_land_cost_per_acre,
          development_cost: parcel.estimated_development_cost,
          itc_value: Math.round(parcel.estimated_development_cost * 0.30),
          estimated_roi_years: Math.round((6 + (100 - overallScore) * 0.08) * 10) / 10
        },
        grid: {
          distance_to_substation: parcel.nearest_substation_mi,
          voltage: parcel.transmission_voltage_kv,
          interconnection_cost: Math.round(parcel.nearest_substation_mi * 150000 + parcel.solar_capacity_mw * 50000)
        }
      },
      duration_seconds: 0.8,
      requested_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    });
  }

  // Fallback for unknown parcels (shouldn't happen with new data)
  const seed = parcel_id.split('').reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0);
  const rng = (mult: number = 1) => ((seed * mult) % 100);

  const permittingScore = 65 + rng(1) % 25;
  const gridScore = 60 + rng(3) % 30;
  const envScore = 70 + rng(7) % 25;
  const landScore = 68 + rng(11) % 27;

  const overallScore = permittingScore * 0.25 + gridScore * 0.30 + envScore * 0.20 + landScore * 0.25;

  return NextResponse.json({
    id: `analysis-${Date.now()}`,
    parcel_id,
    project_type,
    status: 'completed',
    overall_score: Math.round(overallScore * 10) / 10,
    permitting_score: permittingScore,
    grid_score: gridScore,
    environmental_score: envScore,
    land_score: landScore,
    viability: overallScore >= 70 ? 'good' : 'moderate',
    fatal_flaws: [],
    recommendations: [
      'Conduct preliminary site assessment',
      'Engage local planning department',
      'Request utility interconnection study'
    ],
    duration_seconds: 0.8,
    requested_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
  });
}

// Score calculation functions based on architecture document
function calculatePermittingScore(parcel: any): number {
  let score = 50;

  // Zoning compatibility (30%)
  if (parcel.solar_permission === 'By-right') score += 30;
  else if (parcel.solar_permission === 'Conditional Use') score += 20;
  else if (parcel.solar_permission === 'Special Exception') score += 10;
  // Prohibited = 0

  // Land use compatibility (25%)
  const goodLandUse = ['Agricultural', 'Vacant Land', 'Pasture', 'Rangeland'];
  if (goodLandUse.includes(parcel.land_use)) score += 15;
  else score += 5;

  // Add some variance based on state (some states are more solar-friendly)
  const solarFriendlyStates = ['TX', 'CA', 'AZ', 'NM', 'NV', 'FL', 'NC', 'GA'];
  if (solarFriendlyStates.includes(parcel.state_code)) score += 5;

  return Math.min(100, Math.max(0, score));
}

function calculateGridScore(parcel: any): number {
  let score = 0;

  // Distance to substation (35%)
  if (parcel.nearest_substation_mi <= 1) score += 35;
  else if (parcel.nearest_substation_mi <= 3) score += 28;
  else if (parcel.nearest_substation_mi <= 5) score += 21;
  else if (parcel.nearest_substation_mi <= 10) score += 14;
  else score += 7;

  // Transmission voltage (20%)
  if (parcel.transmission_voltage_kv >= 345) score += 20;
  else if (parcel.transmission_voltage_kv >= 230) score += 17;
  else if (parcel.transmission_voltage_kv >= 138) score += 14;
  else if (parcel.transmission_voltage_kv >= 69) score += 10;
  else score += 5;

  // Capacity estimate (30%) - based on solar GHI as proxy
  if (parcel.solar_ghi >= 5.5) score += 30;
  else if (parcel.solar_ghi >= 5.0) score += 25;
  else if (parcel.solar_ghi >= 4.5) score += 20;
  else if (parcel.solar_ghi >= 4.0) score += 15;
  else score += 10;

  // Queue position estimate (15%) - use random but consistent
  score += 10 + (parcel.id.charCodeAt(3) % 5);

  return Math.min(100, Math.max(0, score));
}

function calculateEnvironmentalScore(parcel: any): number {
  let score = 70;

  // Land use affects environmental score
  if (parcel.land_use === 'Agricultural' || parcel.land_use === 'Cropland') score += 15;
  else if (parcel.land_use === 'Pasture' || parcel.land_use === 'Rangeland') score += 12;
  else if (parcel.land_use === 'Vacant Land') score += 10;
  else if (parcel.land_use === 'Forest') score -= 10; // More environmental concerns
  else score += 5;

  // Acreage affects score (larger = more room to avoid sensitive areas)
  if (parcel.acreage >= 500) score += 8;
  else if (parcel.acreage >= 200) score += 5;
  else if (parcel.acreage >= 100) score += 3;

  // Some variance based on location
  const lowRiskStates = ['TX', 'AZ', 'NM', 'NV', 'KS', 'OK'];
  if (lowRiskStates.includes(parcel.state_code)) score += 5;

  return Math.min(100, Math.max(0, score));
}

function calculateLandScore(parcel: any): number {
  let score = 50;

  // Acreage suitability (30%) - optimal is 100-500 acres
  if (parcel.acreage >= 100 && parcel.acreage <= 500) score += 25;
  else if (parcel.acreage >= 50 && parcel.acreage <= 800) score += 20;
  else if (parcel.acreage >= 200) score += 15;
  else score += 10;

  // Land use (25%)
  const idealLandUse = ['Agricultural', 'Pasture', 'Vacant Land'];
  if (idealLandUse.includes(parcel.land_use)) score += 20;
  else if (parcel.land_use === 'Rangeland' || parcel.land_use === 'Cropland') score += 15;
  else score += 5;

  // Owner type (simpler ownership = easier negotiations)
  if (parcel.owner_type === 'Private' || parcel.owner_type === 'Corporate') score += 10;
  else if (parcel.owner_type === 'Trust') score += 5;

  return Math.min(100, Math.max(0, score));
}

function calculateFinancialScore(parcel: any): number {
  let score = 50;

  // Land cost (25%)
  if (parcel.estimated_land_cost_per_acre < 3000) score += 25;
  else if (parcel.estimated_land_cost_per_acre < 5000) score += 20;
  else if (parcel.estimated_land_cost_per_acre < 8000) score += 15;
  else if (parcel.estimated_land_cost_per_acre < 12000) score += 10;
  else score += 5;

  // Solar resource (affects LCOE)
  if (parcel.solar_ghi >= 5.5) score += 20;
  else if (parcel.solar_ghi >= 5.0) score += 15;
  else if (parcel.solar_ghi >= 4.5) score += 10;
  else score += 5;

  // Capacity (economies of scale)
  if (parcel.solar_capacity_mw >= 100) score += 10;
  else if (parcel.solar_capacity_mw >= 50) score += 7;
  else if (parcel.solar_capacity_mw >= 20) score += 5;

  return Math.min(100, Math.max(0, score));
}

function generateRecommendations(parcel: any, scores: any): string[] {
  const recs: string[] = [];

  if (scores.permittingScore < 75) {
    recs.push(`Schedule pre-application meeting with ${parcel.county} County planning department`);
  }

  if (scores.gridScore < 70) {
    recs.push('Request preliminary interconnection study from regional utility');
  }

  if (parcel.nearest_substation_mi > 5) {
    recs.push(`Evaluate transmission line routing options (${parcel.nearest_substation_mi.toFixed(1)} mi to nearest substation)`);
  }

  if (scores.envScore < 80) {
    recs.push('Conduct Phase 1 Environmental Site Assessment');
  }

  if (parcel.solar_permission === 'Conditional Use' || parcel.solar_permission === 'Special Exception') {
    recs.push(`Prepare ${parcel.solar_permission} permit application package`);
  }

  recs.push('Engage landowner for lease term negotiations');

  if (parcel.acreage >= 200) {
    recs.push('Commission preliminary geotechnical and topographic survey');
  }

  if (parcel.solar_ghi >= 5.0 && parcel.wind_speed >= 7.0) {
    recs.push('Consider hybrid solar-wind development to maximize land utilization');
  }

  return recs.slice(0, 6);
}

function identifyFatalFlaws(parcel: any, scores: any): string[] {
  const flaws: string[] = [];

  if (parcel.solar_permission === 'Prohibited') {
    flaws.push('Solar development prohibited under current zoning');
  }

  if (scores.gridScore < 40) {
    flaws.push('Critical grid infrastructure deficiency - no viable interconnection path');
  }

  if (parcel.nearest_substation_mi > 15) {
    flaws.push(`Excessive distance to grid infrastructure (${parcel.nearest_substation_mi.toFixed(1)} miles)`);
  }

  if (scores.envScore < 40) {
    flaws.push('Significant environmental constraints identified');
  }

  if (parcel.acreage < 20) {
    flaws.push('Insufficient acreage for utility-scale development');
  }

  return flaws;
}
