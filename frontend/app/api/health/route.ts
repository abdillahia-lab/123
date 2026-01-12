import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    version: '1.1.0',
    mode: 'demo',
    timestamp: new Date().toISOString(),
  });
}
