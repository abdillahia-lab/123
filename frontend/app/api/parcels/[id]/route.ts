import { NextResponse } from 'next/server';

// Demo parcels data for Virginia
const demoParcels: Record<string, any> = {
  'va-001': {
    id: 'va-001',
    apn: 'VA-LOUD-001-2024',
    state: 'VA',
    county: 'Loudoun',
    municipality: 'Leesburg',
    address: '15200 James Monroe Hwy',
    acreage: 200,
    latitude: 39.1076,
    longitude: -77.5636,
    zoning_type: 'Agricultural',
    solar_permission: 'By-right',
    owner_name: 'Blue Ridge Farms LLC',
    nearest_substation_mi: 2.3,
    created_at: '2024-01-10T10:00:00Z',
  },
  'va-002': {
    id: 'va-002',
    apn: 'VA-FAUQ-002-2024',
    state: 'VA',
    county: 'Fauquier',
    municipality: 'Warrenton',
    address: '8500 Lee Highway',
    acreage: 350,
    latitude: 38.7135,
    longitude: -77.7964,
    zoning_type: 'Rural Agricultural',
    solar_permission: 'Conditional Use',
    owner_name: 'Piedmont Holdings',
    nearest_substation_mi: 4.1,
    created_at: '2024-01-15T14:30:00Z',
  },
  'va-003': {
    id: 'va-003',
    apn: 'VA-CULP-003-2024',
    state: 'VA',
    county: 'Culpeper',
    municipality: 'Culpeper',
    address: '12000 Rixeyville Road',
    acreage: 180,
    latitude: 38.4729,
    longitude: -77.9967,
    zoning_type: 'Agricultural',
    solar_permission: 'By-right',
    owner_name: 'Mountain View Estates',
    nearest_substation_mi: 3.2,
    created_at: '2024-01-20T09:15:00Z',
  },
  'va-004': {
    id: 'va-004',
    apn: 'VA-SPOT-004-2024',
    state: 'VA',
    county: 'Spotsylvania',
    municipality: 'Fredericksburg',
    address: '5500 Courthouse Road',
    acreage: 275,
    latitude: 38.2009,
    longitude: -77.5164,
    zoning_type: 'Agricultural-2',
    solar_permission: 'Special Exception',
    owner_name: 'Colonial Land Trust',
    nearest_substation_mi: 1.8,
    created_at: '2024-01-25T11:45:00Z',
  },
  'va-005': {
    id: 'va-005',
    apn: 'VA-ORAN-005-2024',
    state: 'VA',
    county: 'Orange',
    municipality: 'Orange',
    address: '3200 Constitution Highway',
    acreage: 420,
    latitude: 38.2454,
    longitude: -78.1108,
    zoning_type: 'Rural Agricultural',
    solar_permission: 'By-right',
    owner_name: 'Rapidan Energy Partners',
    nearest_substation_mi: 5.5,
    created_at: '2024-02-01T16:00:00Z',
  },
};

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const parcel = demoParcels[id];

  if (!parcel) {
    return NextResponse.json(
      { detail: 'Parcel not found' },
      { status: 404 }
    );
  }

  return NextResponse.json(parcel);
}
