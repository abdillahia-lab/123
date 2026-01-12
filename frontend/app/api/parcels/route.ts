import { NextRequest, NextResponse } from 'next/server';
import { US_PARCELS, searchParcels, getTotalStatistics, getStateStatistics } from '@/lib/us-parcels-data';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  // Pagination
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '100');
  const offset = (page - 1) * limit;

  // Filters
  const states = searchParams.get('states')?.split(',').filter(Boolean);
  const minAcreage = searchParams.get('minAcreage') ? parseInt(searchParams.get('minAcreage')!) : undefined;
  const maxAcreage = searchParams.get('maxAcreage') ? parseInt(searchParams.get('maxAcreage')!) : undefined;
  const minScore = searchParams.get('minScore') ? parseInt(searchParams.get('minScore')!) : undefined;
  const maxScore = searchParams.get('maxScore') ? parseInt(searchParams.get('maxScore')!) : undefined;
  const viability = searchParams.get('viability')?.split(',').filter(Boolean);
  const permission = searchParams.get('permission')?.split(',').filter(Boolean);
  const text = searchParams.get('q') || searchParams.get('search') || undefined;

  // Apply filters
  let filteredParcels = searchParcels({
    states,
    minAcreage,
    maxAcreage,
    minScore,
    maxScore,
    viability,
    permission,
    text
  });

  // Sort
  const sortBy = searchParams.get('sortBy') || 'overall_score';
  const sortOrder = searchParams.get('sortOrder') || 'desc';

  filteredParcels.sort((a, b) => {
    const aVal = (a as any)[sortBy] ?? 0;
    const bVal = (b as any)[sortBy] ?? 0;
    return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
  });

  // Paginate
  const paginatedParcels = filteredParcels.slice(offset, offset + limit);

  return NextResponse.json({
    parcels: paginatedParcels,
    pagination: {
      page,
      limit,
      total: filteredParcels.length,
      totalPages: Math.ceil(filteredParcels.length / limit),
      hasMore: offset + limit < filteredParcels.length
    },
    meta: {
      totalParcels: US_PARCELS.length,
      filteredCount: filteredParcels.length
    }
  });
}

export async function POST(request: Request) {
  const body = await request.json();

  // Search with POST body for complex queries
  const filteredParcels = searchParcels({
    states: body.states,
    minAcreage: body.minAcreage,
    maxAcreage: body.maxAcreage,
    minScore: body.minScore,
    maxScore: body.maxScore,
    viability: body.viability,
    permission: body.permission,
    minSolarGhi: body.minSolarGhi,
    minWindSpeed: body.minWindSpeed,
    text: body.query || body.text
  });

  const limit = body.limit || 100;
  const offset = body.offset || 0;

  return NextResponse.json({
    parcels: filteredParcels.slice(offset, offset + limit),
    total: filteredParcels.length,
    returned: Math.min(limit, filteredParcels.length - offset)
  });
}
