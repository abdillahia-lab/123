import { NextResponse } from 'next/server';

// Simulate analysis delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function POST(request: Request) {
  const body = await request.json();
  const { parcel_id, project_type = 'utility_solar' } = body;

  // Simulate analysis time
  await delay(500);

  // Generate realistic scores based on random seed
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
  let starRating = 3;
  let recommendation = 'proceed_with_caution';

  if (overallScore >= 80) {
    viability = 'good';
    starRating = 4;
    recommendation = 'proceed';
  } else if (overallScore >= 90) {
    viability = 'excellent';
    starRating = 5;
    recommendation = 'proceed';
  } else if (overallScore < 50) {
    viability = 'challenging';
    starRating = 2;
    recommendation = 'do_not_proceed';
  }

  const analysis = {
    id: `analysis-${Date.now()}`,
    parcel_id,
    project_type,
    requested_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    duration_seconds: 0.5,
    score: {
      overall_score: Math.round(overallScore * 10) / 10,
      viability,
      star_rating: starRating,
      permitting_score: permittingScore,
      grid_score: gridScore,
      environmental_score: envScore,
      land_score: landScore,
      financial_score: 0,
      confidence: 0.85,
      data_completeness: 0.92,
      fatal_flaws: [],
      major_risks: overallScore < 70 ? ['Grid capacity constraints identified'] : [],
      minor_risks: ['Conditional use permit required'],
      opportunities: ['Strong solar resource', 'Nearby transmission infrastructure'],
    },
    proceed_recommendation: recommendation,
    recommended_next_steps: [
      'Contact county planning department',
      'Request preliminary interconnection study',
      'Conduct Phase 1 environmental assessment',
      'Engage landowner for lease negotiations',
    ],
    requires_human_review: overallScore < 60 || overallScore > 90,
    review_reasons: overallScore > 90 ? ['High-value opportunity detected'] : [],
    agents_executed: ['permitting', 'grid', 'environmental', 'land'],
    agent_durations: {
      permitting: 0.12,
      grid: 0.15,
      environmental: 0.11,
      land: 0.09,
    },
  };

  return NextResponse.json(analysis);
}
