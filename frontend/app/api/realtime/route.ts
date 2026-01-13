import { NextResponse } from 'next/server';
import { isoClient, getISORegionForState, type ISORegion } from '@/lib/realtime/iso-client';

export const dynamic = 'force-dynamic';

// GET /api/realtime - Get current market data
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const dataType = searchParams.get('type') || 'summary';
  const region = searchParams.get('region') as ISORegion | null;
  const state = searchParams.get('state');

  try {
    // If state provided, determine region
    const targetRegion = region || (state ? getISORegionForState(state) : null);

    switch (dataType) {
      case 'lmp': {
        if (targetRegion) {
          const result = await isoClient.getLMP(targetRegion);
          if (!result.success) throw result.error;
          return NextResponse.json({ region: targetRegion, data: result.data });
        }
        // Get all regions
        const allLmp = await isoClient.getAllRegionsLMP();
        return NextResponse.json({
          data: Object.fromEntries(allLmp),
          timestamp: new Date().toISOString(),
        });
      }

      case 'load': {
        if (targetRegion) {
          const result = await isoClient.getGridLoad(targetRegion);
          if (!result.success) throw result.error;
          return NextResponse.json({ region: targetRegion, data: result.data });
        }
        // Get all regions
        const allLoad = await isoClient.getAllRegionsLoad();
        return NextResponse.json({
          data: Object.fromEntries(allLoad),
          timestamp: new Date().toISOString(),
        });
      }

      case 'queue': {
        const fuelType = searchParams.get('fuelType') as 'Solar' | 'Wind' | 'Storage' | 'Hybrid' | null;
        const minCapacity = searchParams.get('minCapacity');
        const status = searchParams.get('status') as 'Active' | 'Withdrawn' | 'Completed' | null;

        if (targetRegion) {
          const result = await isoClient.getInterconnectionQueue(targetRegion, {
            fuelType: fuelType || undefined,
            minCapacity: minCapacity ? parseInt(minCapacity) : undefined,
            status: status || undefined,
          });
          if (!result.success) throw result.error;
          return NextResponse.json({
            region: targetRegion,
            projects: result.data,
            count: result.data.length,
          });
        }
        // Get queue stats across all regions
        const stats = await isoClient.getQueueStats();
        return NextResponse.json(stats);
      }

      case 'summary':
      default: {
        // Get summary across all regions
        const [lmpData, loadData, queueStats] = await Promise.all([
          isoClient.getAllRegionsLMP(),
          isoClient.getAllRegionsLoad(),
          isoClient.getQueueStats(),
        ]);

        // Calculate average LMP per region
        const avgLmpByRegion: Record<string, number> = {};
        lmpData.forEach((lmps, region) => {
          const avg = lmps.reduce((sum, l) => sum + l.lmpTotal, 0) / lmps.length;
          avgLmpByRegion[region] = Math.round(avg * 100) / 100;
        });

        // Get total renewable generation
        let totalSolar = 0;
        let totalWind = 0;
        let totalLoad = 0;
        loadData.forEach(load => {
          totalSolar += load.renewableGeneration.solar;
          totalWind += load.renewableGeneration.wind;
          totalLoad += load.currentLoad;
        });

        return NextResponse.json({
          timestamp: new Date().toISOString(),
          market: {
            avgLmpByRegion,
            priceRange: {
              min: Math.min(...Object.values(avgLmpByRegion)),
              max: Math.max(...Object.values(avgLmpByRegion)),
            },
          },
          grid: {
            totalLoadMw: Math.round(totalLoad),
            totalSolarMw: Math.round(totalSolar),
            totalWindMw: Math.round(totalWind),
            renewablePenetration: Math.round(((totalSolar + totalWind) / totalLoad) * 100),
          },
          interconnection: {
            totalProjects: queueStats.totalProjects,
            totalCapacityMw: queueStats.totalCapacityMw,
            byFuelType: queueStats.byFuelType,
            activeVsWithdrawn: queueStats.activeVsWithdrawn,
          },
        });
      }
    }
  } catch (error) {
    console.error('[API/realtime] Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch real-time data' },
      { status: 500 }
    );
  }
}
