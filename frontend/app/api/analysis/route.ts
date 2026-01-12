import { NextResponse } from 'next/server';

// Simulate analysis delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function POST(request: Request) {
  const body = await request.json();
  const { parcel_id, project_type = 'utility_solar' } = body;

  // Simulate analysis time
  await delay(500);

  // Generate realistic scores based on parcel ID
  const seed = parcel_id.charCodeAt(parcel_id.length - 1);
  const permittingScore = 65 + (seed % 25);
  const gridScore = 60 + ((seed * 3) % 30);
  const envScore = 70 + ((seed * 7) % 25);
  const landScore = 68 + ((seed * 11) % 27);

  const overallScore = (
    permittingScore * 0.30 +
    gridScore * 0.30 +
    envScore * 0.20 +
    landScore * 0.20
  );

  let viability = 'moderate';
  if (overallScore >= 85) {
    viability = 'excellent';
  } else if (overallScore >= 70) {
    viability = 'good';
  } else if (overallScore < 50) {
    viability = 'challenging';
  }

  // Generate recommendations based on scores
  const recommendations: string[] = [];
  if (permittingScore < 75) {
    recommendations.push('Contact county planning department for pre-application meeting');
  }
  if (gridScore < 70) {
    recommendations.push('Request preliminary interconnection study from utility');
  }
  if (envScore < 80) {
    recommendations.push('Conduct Phase 1 environmental site assessment');
  }
  recommendations.push('Engage landowner for lease term negotiations');
  recommendations.push('Commission preliminary geotechnical survey');

  // Generate fatal flaws (only for very low scores)
  const fatal_flaws: string[] = [];
  if (gridScore < 50) {
    fatal_flaws.push('No viable grid interconnection point within 10 miles');
  }
  if (envScore < 45) {
    fatal_flaws.push('Site overlaps with protected wetlands');
  }

  // Return flat structure matching AnalysisPanel expectations
  const analysis = {
    id: `analysis-${Date.now()}`,
    parcel_id,
    project_type,
    status: 'completed',
    overall_score: Math.round(overallScore * 10) / 10,
    permitting_score: permittingScore,
    grid_score: gridScore,
    environmental_score: envScore,
    land_score: landScore,
    viability,
    fatal_flaws,
    recommendations,
    duration_seconds: 0.5,
    requested_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
  };

  return NextResponse.json(analysis);
}
