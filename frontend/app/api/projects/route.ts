import { NextResponse } from 'next/server';

// Demo projects for Virginia
const demoProjects = [
  {
    id: 'proj-001',
    name: 'Loudoun Solar Farm',
    project_type: 'utility_solar',
    stage: 'due_diligence',
    parcel_ids: ['va-001'],
    total_acreage: 200,
    capacity_mw: 50,
    state: 'VA',
    county: 'Loudoun',
    created_at: '2024-01-10T10:00:00Z',
  },
  {
    id: 'proj-002',
    name: 'Wythe Valley Energy',
    project_type: 'utility_solar',
    stage: 'prospecting',
    parcel_ids: ['va-002'],
    total_acreage: 350,
    capacity_mw: 75,
    state: 'VA',
    county: 'Wythe',
    created_at: '2024-01-08T14:30:00Z',
  },
  {
    id: 'proj-003',
    name: 'Augusta Renewables',
    project_type: 'solar_plus_storage',
    stage: 'site_control',
    parcel_ids: ['va-003'],
    total_acreage: 275,
    capacity_mw: 60,
    state: 'VA',
    county: 'Augusta',
    created_at: '2024-01-05T09:15:00Z',
  },
  {
    id: 'proj-004',
    name: 'Pittsylvania Power',
    project_type: 'utility_solar',
    stage: 'permitting',
    parcel_ids: ['va-004'],
    total_acreage: 180,
    capacity_mw: 40,
    state: 'VA',
    county: 'Pittsylvania',
    created_at: '2024-01-01T11:45:00Z',
  },
];

export async function GET() {
  return NextResponse.json(demoProjects);
}

export async function POST(request: Request) {
  const body = await request.json();

  const newProject = {
    id: `proj-${Date.now()}`,
    ...body,
    stage: 'prospecting',
    parcel_ids: [],
    total_acreage: 0,
    capacity_mw: 0,
    created_at: new Date().toISOString(),
  };

  return NextResponse.json(newProject, { status: 201 });
}
