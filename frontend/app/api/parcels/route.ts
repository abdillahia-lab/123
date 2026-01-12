import { NextResponse } from 'next/server';

// Demo parcels for Virginia
const demoParcels = [
  {
    id: 'va-001',
    apn: '123-45-6789',
    state: 'VA',
    county: 'Loudoun',
    address: '1234 Solar Valley Rd, Leesburg, VA',
    acreage: 200,
    zoning_type: 'agricultural',
    solar_permission: 'conditional_use',
    centroid: { latitude: 39.1157, longitude: -77.5636 },
    score: 71,
    viability: 'moderate',
  },
  {
    id: 'va-002',
    apn: '234-56-7890',
    state: 'VA',
    county: 'Wythe',
    address: 'Rural Route 5, Wytheville, VA',
    acreage: 350,
    zoning_type: 'agricultural',
    solar_permission: 'by_right',
    centroid: { latitude: 36.9487, longitude: -81.0848 },
    score: 85,
    viability: 'good',
  },
  {
    id: 'va-003',
    apn: '345-67-8901',
    state: 'VA',
    county: 'Augusta',
    address: '5678 Farm Lane, Staunton, VA',
    acreage: 275,
    zoning_type: 'agricultural',
    solar_permission: 'conditional_use',
    centroid: { latitude: 38.1496, longitude: -79.0717 },
    score: 78,
    viability: 'good',
  },
  {
    id: 'va-004',
    apn: '456-78-9012',
    state: 'VA',
    county: 'Pittsylvania',
    address: '9012 Tobacco Rd, Danville, VA',
    acreage: 180,
    zoning_type: 'agricultural',
    solar_permission: 'by_right',
    centroid: { latitude: 36.5860, longitude: -79.3950 },
    score: 82,
    viability: 'good',
  },
  {
    id: 'va-005',
    apn: '567-89-0123',
    state: 'VA',
    county: 'Fairfax',
    address: '7890 Tysons Blvd, McLean, VA',
    acreage: 25,
    zoning_type: 'commercial',
    solar_permission: 'conditional_use',
    centroid: { latitude: 38.9217, longitude: -77.2297 },
    score: 58,
    viability: 'moderate',
  },
];

export async function GET() {
  return NextResponse.json(demoParcels);
}

export async function POST(request: Request) {
  const body = await request.json();

  const newParcel = {
    id: `va-${Date.now()}`,
    ...body,
    score: Math.floor(Math.random() * 30) + 60,
    viability: 'moderate',
  };

  return NextResponse.json(newParcel, { status: 201 });
}
