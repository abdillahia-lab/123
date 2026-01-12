import { NextRequest, NextResponse } from 'next/server';
import { getParcelById } from '@/lib/us-parcels-data';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const parcel = getParcelById(id);

  if (!parcel) {
    return NextResponse.json(
      { error: 'Parcel not found', id },
      { status: 404 }
    );
  }

  // Seeded random for consistent computed values
  let seed = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const rng = () => {
    const x = Math.sin(seed++) * 10000;
    return x - Math.floor(x);
  };

  // Return detailed parcel info with computed fields
  return NextResponse.json({
    ...parcel,
    // Additional computed fields for detail view
    details: {
      solar: {
        capacity_mw: parcel.solar_capacity_mw,
        annual_production_mwh: Math.round(parcel.solar_capacity_mw * parcel.solar_ghi * 365 * 0.2),
        capacity_factor: Math.round((parcel.solar_ghi / 6.5) * 25 * 10) / 10,
        estimated_revenue: Math.round(parcel.solar_capacity_mw * parcel.solar_ghi * 365 * 0.2 * 45),
      },
      wind: {
        capacity_mw: parcel.wind_capacity_mw,
        annual_production_mwh: Math.round(parcel.wind_capacity_mw * parcel.wind_speed * 365 * 0.35),
        capacity_factor: Math.round((parcel.wind_speed / 8.5) * 35 * 10) / 10,
        estimated_revenue: Math.round(parcel.wind_capacity_mw * parcel.wind_speed * 365 * 0.35 * 40),
      },
      financial: {
        land_cost: parcel.acreage * parcel.estimated_land_cost_per_acre,
        development_cost: parcel.estimated_development_cost,
        total_project_cost: parcel.acreage * parcel.estimated_land_cost_per_acre + parcel.estimated_development_cost,
        itc_value: Math.round(parcel.estimated_development_cost * 0.30),
        estimated_lcoe: Math.round((25 + rng() * 15) * 10) / 10,
        payback_years: Math.round((5 + rng() * 5) * 10) / 10,
      },
      grid: {
        nearest_substation_mi: parcel.nearest_substation_mi,
        transmission_voltage_kv: parcel.transmission_voltage_kv,
        estimated_interconnection_cost: Math.round(parcel.nearest_substation_mi * 150000 + parcel.solar_capacity_mw * 50000),
        queue_position_estimate: Math.floor(rng() * 300) + 50,
      },
      environmental: {
        wetlands_percentage: Math.round(rng() * 10),
        flood_zone: ['Zone X', 'Zone X', 'Zone X', 'Zone B', 'Zone A'][Math.floor(rng() * 5)],
        endangered_species_risk: ['None', 'None', 'Low', 'Low', 'Moderate'][Math.floor(rng() * 5)],
        cultural_resources: ['None', 'None', 'None', 'Low', 'Moderate'][Math.floor(rng() * 5)],
      }
    }
  });
}
