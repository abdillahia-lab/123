import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    parcels_count: 5,
    projects_count: 2,
    analyses_count: 12,
    config: {
      mode: 'demo',
      version: '1.1.0',
    },
  });
}
