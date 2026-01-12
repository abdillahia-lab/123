import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    parcels_count: 5,
    projects_count: 4,
    analyses_count: 23,
    high_value_sites: 2,
    config: {
      mode: 'demo',
      version: '1.1.0',
    },
  });
}
