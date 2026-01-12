import { NextResponse } from 'next/server';
import { getTotalStatistics, getStateStatistics, US_PARCELS } from '@/lib/us-parcels-data';

export async function GET() {
  const total = getTotalStatistics();
  const byState = getStateStatistics();

  // Top states by score
  const topStates = Object.entries(byState)
    .map(([code, stats]) => ({ code, ...stats }))
    .sort((a, b) => b.avgScore - a.avgScore)
    .slice(0, 10);

  // Recent high-value discoveries
  const highValueParcels = US_PARCELS
    .filter(p => p.overall_score >= 80)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return NextResponse.json({
    overview: {
      total_parcels: total.parcelCount,
      total_states: total.stateCount,
      total_acreage: total.totalAcreage,
      total_solar_capacity_mw: total.totalSolarCapacity,
      total_wind_capacity_mw: total.totalWindCapacity,
      average_score: total.avgScore,
      excellent_sites: total.excellentCount,
      good_sites: total.goodCount,
      moderate_sites: total.moderateCount,
    },
    // Legacy fields for backward compatibility
    parcels_count: total.parcelCount,
    projects_count: 12,
    analyses_count: total.excellentCount + total.goodCount,
    high_value_sites: total.excellentCount,
    distribution: {
      by_viability: {
        excellent: total.excellentCount,
        good: total.goodCount,
        moderate: total.moderateCount,
        challenging: total.parcelCount - total.excellentCount - total.goodCount - total.moderateCount,
      },
      by_region: {
        southwest: ['AZ', 'NM', 'NV', 'UT', 'CO'].reduce((sum, s) => sum + (byState[s]?.count || 0), 0),
        midwest: ['IA', 'KS', 'NE', 'SD', 'ND', 'MN', 'WI', 'IL', 'IN', 'OH', 'MI'].reduce((sum, s) => sum + (byState[s]?.count || 0), 0),
        south: ['TX', 'OK', 'AR', 'LA', 'MS', 'AL', 'TN', 'KY', 'WV', 'VA', 'NC', 'SC', 'GA', 'FL'].reduce((sum, s) => sum + (byState[s]?.count || 0), 0),
        west: ['CA', 'OR', 'WA', 'ID', 'MT', 'WY'].reduce((sum, s) => sum + (byState[s]?.count || 0), 0),
        northeast: ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA', 'DE', 'MD'].reduce((sum, s) => sum + (byState[s]?.count || 0), 0),
      }
    },
    top_states: topStates,
    recent_high_value: highValueParcels.map(p => ({
      id: p.id,
      state: p.state,
      county: p.county,
      acreage: p.acreage,
      score: p.overall_score,
      capacity_mw: p.solar_capacity_mw
    })),
    config: {
      mode: 'demo',
      version: '2.0.0',
      data_source: 'TerraJinki US Dataset',
      last_updated: new Date().toISOString()
    }
  });
}
