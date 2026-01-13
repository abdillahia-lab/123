import { NextResponse } from 'next/server';
import { alertService, alertTemplates, type AlertCriteria } from '@/lib/realtime/parcel-alerts';

export const dynamic = 'force-dynamic';

// GET /api/alerts - Get user's alert subscriptions
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get('userId') || 'demo-user';
  const subscriptionId = searchParams.get('subscriptionId');

  try {
    if (subscriptionId) {
      // Get matches for a specific subscription
      const result = await alertService.getSubscriptionMatches(subscriptionId);
      if (!result.success) throw result.error;
      return NextResponse.json({
        subscriptionId,
        matches: result.data,
        count: result.data.length,
      });
    }

    // Get all user subscriptions
    const result = await alertService.getUserSubscriptions(userId);
    if (!result.success) throw result.error;

    return NextResponse.json({
      userId,
      subscriptions: result.data,
      count: result.data.length,
      templates: Object.entries(alertTemplates).map(([key, template]) => ({
        id: key,
        name: template.name,
        criteria: template.criteria,
      })),
    });
  } catch (error) {
    console.error('[API/alerts] Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch alerts' },
      { status: 500 }
    );
  }
}

// POST /api/alerts - Create a new alert subscription
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      userId = 'demo-user',
      name,
      criteria,
      channels = { email: true, push: false, inApp: true },
      frequency = 'daily',
      templateId,
    } = body;

    // Use template if provided
    let alertCriteria: AlertCriteria = criteria;
    let alertName = name;

    if (templateId && alertTemplates[templateId]) {
      const template = alertTemplates[templateId];
      alertCriteria = { ...template.criteria, ...criteria };
      alertName = name || template.name;
    }

    if (!alertName) {
      return NextResponse.json(
        { error: 'Subscription name is required' },
        { status: 400 }
      );
    }

    const result = await alertService.createSubscription(
      userId,
      alertName,
      alertCriteria,
      channels,
      frequency
    );

    if (!result.success) throw result.error;

    return NextResponse.json({
      success: true,
      subscription: result.data,
    });
  } catch (error) {
    console.error('[API/alerts] Error creating subscription:', error);
    return NextResponse.json(
      { error: 'Failed to create subscription' },
      { status: 500 }
    );
  }
}

// PATCH /api/alerts - Update a subscription
export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { subscriptionId, ...updates } = body;

    if (!subscriptionId) {
      return NextResponse.json(
        { error: 'Subscription ID is required' },
        { status: 400 }
      );
    }

    const result = await alertService.updateSubscription(subscriptionId, updates);
    if (!result.success) throw result.error;

    return NextResponse.json({
      success: true,
      subscription: result.data,
    });
  } catch (error) {
    console.error('[API/alerts] Error updating subscription:', error);
    return NextResponse.json(
      { error: 'Failed to update subscription' },
      { status: 500 }
    );
  }
}

// DELETE /api/alerts - Delete a subscription
export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const subscriptionId = searchParams.get('subscriptionId');

  if (!subscriptionId) {
    return NextResponse.json(
      { error: 'Subscription ID is required' },
      { status: 400 }
    );
  }

  try {
    const result = await alertService.deleteSubscription(subscriptionId);
    if (!result.success) throw result.error;

    return NextResponse.json({
      success: true,
      deleted: subscriptionId,
    });
  } catch (error) {
    console.error('[API/alerts] Error deleting subscription:', error);
    return NextResponse.json(
      { error: 'Failed to delete subscription' },
      { status: 500 }
    );
  }
}
