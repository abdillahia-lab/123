import { NextResponse } from 'next/server';

// Demo parcels data
const demoParcels = [
  {
    id: 'va-001',
    apn: 'VA-LOUD-001-2024',
    state: 'VA',
    county: 'Loudoun',
    municipality: 'Leesburg',
    address: '15200 James Monroe Hwy',
    acreage: 200,
    zoning_type: 'Agricultural',
    solar_permission: 'By-right',
    owner_name: 'Blue Ridge Farms LLC',
    created_at: '2024-01-10T10:00:00Z',
  },
  {
    id: 'va-002',
    apn: 'VA-FAUQ-002-2024',
    state: 'VA',
    county: 'Fauquier',
    municipality: 'Warrenton',
    address: '8500 Lee Highway',
    acreage: 350,
    zoning_type: 'Rural Agricultural',
    solar_permission: 'Conditional Use',
    owner_name: 'Piedmont Holdings',
    created_at: '2024-01-15T14:30:00Z',
  },
  {
    id: 'va-003',
    apn: 'VA-CULP-003-2024',
    state: 'VA',
    county: 'Culpeper',
    municipality: 'Culpeper',
    address: '12000 Rixeyville Road',
    acreage: 180,
    zoning_type: 'Agricultural',
    solar_permission: 'By-right',
    owner_name: 'Mountain View Estates',
    created_at: '2024-01-20T09:15:00Z',
  },
  {
    id: 'va-004',
    apn: 'VA-SPOT-004-2024',
    state: 'VA',
    county: 'Spotsylvania',
    municipality: 'Fredericksburg',
    address: '5500 Courthouse Road',
    acreage: 275,
    zoning_type: 'Agricultural-2',
    solar_permission: 'Special Exception',
    owner_name: 'Colonial Land Trust',
    created_at: '2024-01-25T11:45:00Z',
  },
  {
    id: 'va-005',
    apn: 'VA-ORAN-005-2024',
    state: 'VA',
    county: 'Orange',
    municipality: 'Orange',
    address: '3200 Constitution Highway',
    acreage: 420,
    zoning_type: 'Rural Agricultural',
    solar_permission: 'By-right',
    owner_name: 'Rapidan Energy Partners',
    created_at: '2024-02-01T16:00:00Z',
  },
];

export async function POST(request: Request) {
  const startTime = Date.now();
  const body = await request.json();

  let results = [...demoParcels];

  // Filter by states
  if (body.states && body.states.length > 0) {
    results = results.filter(p => body.states.includes(p.state));
  }

  // Filter by counties
  if (body.counties && body.counties.length > 0) {
    results = results.filter(p =>
      body.counties.some((c: string) => p.county.toLowerCase().includes(c.toLowerCase()))
    );
  }

  // Filter by acreage
  if (body.min_acreage) {
    results = results.filter(p => p.acreage >= body.min_acreage);
  }
  if (body.max_acreage) {
    results = results.filter(p => p.acreage <= body.max_acreage);
  }

  // Text search in query
  if (body.query) {
    const q = body.query.toLowerCase();
    results = results.filter(p =>
      p.county.toLowerCase().includes(q) ||
      p.municipality.toLowerCase().includes(q) ||
      p.owner_name.toLowerCase().includes(q) ||
      p.state.toLowerCase().includes(q)
    );
  }

  // Apply limit and offset
  const offset = body.offset || 0;
  const limit = body.limit || 50;
  const paginatedResults = results.slice(offset, offset + limit);

  return NextResponse.json({
    total_matches: results.length,
    returned_count: paginatedResults.length,
    parcels: paginatedResults,
    interpreted_query: body.query || 'All Virginia parcels',
    search_duration_ms: Date.now() - startTime,
  });
}
