'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap,
  TrendingUp,
  TrendingDown,
  Bell,
  Clock,
  MapPin,
  DollarSign,
  Activity,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  Sun,
  Wind,
  Battery,
  RefreshCw,
  Eye,
  Star,
  Plus,
} from 'lucide-react';
import { useMarketStream, type PriceAlert as StreamPriceAlert } from '@/lib/realtime/market-stream';
import type { ISORegion } from '@/lib/realtime/iso-client';

// ============================================================================
// TYPES
// ============================================================================

interface MarketPrice {
  region: string;
  price: number;
  change: number;
  trend: 'up' | 'down' | 'stable';
}

interface NewOpportunity {
  id: string;
  state: string;
  county: string;
  acreage: number;
  score: number;
  capacityMw: number;
  viability: 'excellent' | 'good' | 'moderate';
  detectedAt: string;
  matchedAlerts: string[];
}

interface AlertMatch {
  id: string;
  alertName: string;
  parcelCount: number;
  topMatch: {
    state: string;
    county: string;
    score: number;
  };
  timestamp: string;
}

interface GridStatus {
  region: string;
  load: number;
  capacity: number;
  renewablePct: number;
  status: 'normal' | 'stressed' | 'critical';
}

// ============================================================================
// LIVE INDICATOR COMPONENT
// ============================================================================

function LiveIndicator({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
      </span>
      {label && <span className="text-xs text-green-600 dark:text-green-400 font-medium">{label}</span>}
    </div>
  );
}

// ============================================================================
// MARKET TICKER
// ============================================================================

function MarketTicker({ prices }: { prices: MarketPrice[] }) {
  return (
    <div className="flex items-center gap-6 overflow-x-auto py-2 px-4 bg-gray-900 text-white text-sm">
      <LiveIndicator label="LIVE" />
      <div className="flex items-center gap-6">
        {prices.map((price) => (
          <div key={price.region} className="flex items-center gap-2 whitespace-nowrap">
            <span className="text-gray-400">{price.region}</span>
            <span className="font-mono font-medium">${price.price.toFixed(2)}</span>
            <span className={`flex items-center text-xs ${
              price.trend === 'up' ? 'text-green-400' : price.trend === 'down' ? 'text-red-400' : 'text-gray-400'
            }`}>
              {price.trend === 'up' ? <TrendingUp className="w-3 h-3" /> :
               price.trend === 'down' ? <TrendingDown className="w-3 h-3" /> : null}
              {price.change > 0 ? '+' : ''}{price.change.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// OPPORTUNITY CARD
// ============================================================================

function OpportunityCard({ opportunity, onView }: { opportunity: NewOpportunity; onView: () => void }) {
  const timeAgo = getTimeAgo(opportunity.detectedAt);
  const isHot = opportunity.matchedAlerts.length > 0;

  return (
    <div
      className={`
        relative p-4 rounded-xl border transition-all cursor-pointer
        hover:shadow-lg hover:border-terra-500 group
        ${isHot
          ? 'bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 border-orange-200 dark:border-orange-800'
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'}
      `}
      onClick={onView}
    >
      {isHot && (
        <div className="absolute -top-2 -right-2 px-2 py-0.5 bg-orange-500 text-white text-xs font-bold rounded-full flex items-center gap-1">
          <Zap className="w-3 h-3" />
          HOT
        </div>
      )}

      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-gray-400" />
            <span className="font-semibold text-gray-900 dark:text-white">
              {opportunity.county}, {opportunity.state}
            </span>
          </div>
          <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            {timeAgo}
          </div>
        </div>
        <div className={`
          px-2.5 py-1 rounded-lg text-sm font-bold
          ${opportunity.score >= 85 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
            opportunity.score >= 70 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
            'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}
        `}>
          {opportunity.score}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Acres</div>
          <div className="font-semibold text-gray-900 dark:text-white">{opportunity.acreage.toLocaleString()}</div>
        </div>
        <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Capacity</div>
          <div className="font-semibold text-gray-900 dark:text-white">{opportunity.capacityMw} MW</div>
        </div>
        <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Viability</div>
          <div className={`font-semibold capitalize ${
            opportunity.viability === 'excellent' ? 'text-green-600' :
            opportunity.viability === 'good' ? 'text-yellow-600' : 'text-gray-600'
          }`}>
            {opportunity.viability}
          </div>
        </div>
      </div>

      {opportunity.matchedAlerts.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-orange-600 dark:text-orange-400">
          <Bell className="w-3 h-3" />
          Matches: {opportunity.matchedAlerts.join(', ')}
        </div>
      )}

      <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <ChevronRight className="w-5 h-5 text-terra-600" />
      </div>
    </div>
  );
}

// ============================================================================
// ALERT NOTIFICATION CARD
// ============================================================================

function AlertNotificationCard({ alert, onView }: { alert: AlertMatch; onView: () => void }) {
  return (
    <div
      className="flex items-center gap-3 p-3 bg-terra-50 dark:bg-terra-900/20 border border-terra-200 dark:border-terra-800 rounded-lg cursor-pointer hover:bg-terra-100 dark:hover:bg-terra-900/30 transition-colors"
      onClick={onView}
    >
      <div className="p-2 bg-terra-500 rounded-lg">
        <Bell className="w-4 h-4 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-gray-900 dark:text-white truncate">{alert.alertName}</div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {alert.parcelCount} new {alert.parcelCount === 1 ? 'match' : 'matches'}
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm font-semibold text-terra-600 dark:text-terra-400">
          {alert.topMatch.score}
        </div>
        <div className="text-xs text-gray-500">{alert.topMatch.state}</div>
      </div>
    </div>
  );
}

// ============================================================================
// GRID STATUS CARD
// ============================================================================

function GridStatusCard({ status }: { status: GridStatus }) {
  const utilizationPct = (status.load / status.capacity) * 100;

  return (
    <div className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900 dark:text-white">{status.region}</span>
        <span className={`
          px-2 py-0.5 text-xs font-medium rounded-full
          ${status.status === 'normal' ? 'bg-green-100 text-green-700' :
            status.status === 'stressed' ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'}
        `}>
          {status.status}
        </span>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Load: {(status.load / 1000).toFixed(1)} GW</span>
          <span>{utilizationPct.toFixed(0)}%</span>
        </div>
        <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              utilizationPct > 90 ? 'bg-red-500' :
              utilizationPct > 75 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(utilizationPct, 100)}%` }}
          />
        </div>
        <div className="flex items-center gap-1 text-xs text-green-600">
          <Sun className="w-3 h-3" />
          {status.renewablePct}% renewable
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// QUICK ACTION BUTTON
// ============================================================================

function QuickActionButton({
  icon: Icon,
  label,
  description,
  onClick,
  variant = 'default'
}: {
  icon: React.ElementType;
  label: string;
  description: string;
  onClick: () => void;
  variant?: 'default' | 'primary' | 'warning';
}) {
  const variants = {
    default: 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-terra-500',
    primary: 'bg-gradient-to-r from-terra-500 to-jinki-500 border-transparent text-white',
    warning: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800 hover:border-orange-500',
  };

  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-3 p-4 rounded-xl border transition-all
        ${variants[variant]}
        ${variant !== 'primary' ? 'hover:shadow-md' : 'hover:opacity-90'}
      `}
    >
      <div className={`p-2 rounded-lg ${
        variant === 'primary' ? 'bg-white/20' : 'bg-terra-100 dark:bg-terra-900/30'
      }`}>
        <Icon className={`w-5 h-5 ${
          variant === 'primary' ? 'text-white' : 'text-terra-600 dark:text-terra-400'
        }`} />
      </div>
      <div className="text-left">
        <div className={`font-semibold ${
          variant === 'primary' ? 'text-white' : 'text-gray-900 dark:text-white'
        }`}>
          {label}
        </div>
        <div className={`text-sm ${
          variant === 'primary' ? 'text-white/80' : 'text-gray-500 dark:text-gray-400'
        }`}>
          {description}
        </div>
      </div>
    </button>
  );
}

// ============================================================================
// PRICE TREND CHART (Mini Sparkline)
// ============================================================================

function PriceTrendChart({ data, color = 'terra' }: { data: number[]; color?: 'terra' | 'green' | 'red' }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  const colorClasses = {
    terra: 'stroke-terra-500',
    green: 'stroke-green-500',
    red: 'stroke-red-500',
  };

  return (
    <svg viewBox="0 0 100 100" className="w-full h-12" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        className={colorClasses[color]}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

// ============================================================================
// MARKET OVERVIEW CHART
// ============================================================================

function MarketOverviewChart({ prices }: { prices: MarketPrice[] }) {
  // Generate mock historical data for each region
  const generateHistory = (currentPrice: number) => {
    const history: number[] = [];
    let price = currentPrice * 0.9;
    for (let i = 0; i < 24; i++) {
      price += (Math.random() - 0.45) * 5;
      history.push(Math.max(0, price));
    }
    history.push(currentPrice);
    return history;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-white">24h Price Trends</h3>
        <span className="text-xs text-gray-500">$/MWh</span>
      </div>
      <div className="space-y-4">
        {prices.slice(0, 4).map((price) => {
          const history = generateHistory(price.price);
          const trend = price.change >= 0 ? 'green' : 'red';
          return (
            <div key={price.region} className="flex items-center gap-4">
              <div className="w-16 text-sm font-medium text-gray-700 dark:text-gray-300">
                {price.region}
              </div>
              <div className="flex-1">
                <PriceTrendChart data={history} color={trend} />
              </div>
              <div className="text-right w-20">
                <div className="font-mono font-semibold text-gray-900 dark:text-white">
                  ${price.price.toFixed(2)}
                </div>
                <div className={`text-xs ${price.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {price.change >= 0 ? '+' : ''}{price.change.toFixed(1)}%
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// ALERT BUILDER MODAL
// ============================================================================

function AlertBuilderModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [states, setStates] = useState<string[]>([]);
  const [minAcreage, setMinAcreage] = useState(100);
  const [minScore, setMinScore] = useState(70);

  const templates = [
    { id: 'texas-solar', name: 'Texas Solar', description: 'Large solar sites in ERCOT', icon: Sun },
    { id: 'midwest-wind', name: 'Midwest Wind', description: 'Wind opportunities in SPP/MISO', icon: Wind },
    { id: 'grid-ready', name: 'Grid-Ready', description: 'Sites near existing transmission', icon: Zap },
    { id: 'premium-sites', name: 'Premium Sites', description: 'Highest scoring opportunities', icon: Star },
  ];

  const stateOptions = ['TX', 'CA', 'AZ', 'NV', 'FL', 'NC', 'OH', 'IL', 'IA', 'OK'];

  const handleCreate = async () => {
    if (!name.trim()) return;
    setIsCreating(true);

    try {
      const response = await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          template: selectedTemplate,
          criteria: {
            states: states.length > 0 ? states : undefined,
            minAcreage,
            minScore,
          },
          channels: { email: true, inApp: true },
          frequency: 'instant',
        }),
      });

      if (response.ok) {
        onCreated();
      }
    } catch (error) {
      console.error('Failed to create alert:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Create Alert</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              <ChevronRight className="w-5 h-5 rotate-45" />
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">Get notified when new sites match your criteria</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Name Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Alert Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Premium Texas Sites"
              className="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-terra-500 focus:border-transparent"
            />
          </div>

          {/* Templates */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quick Templates
            </label>
            <div className="grid grid-cols-2 gap-2">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => setSelectedTemplate(template.id === selectedTemplate ? null : template.id)}
                  className={`
                    flex items-center gap-2 p-3 rounded-xl border text-left transition-all
                    ${selectedTemplate === template.id
                      ? 'border-terra-500 bg-terra-50 dark:bg-terra-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-terra-300'}
                  `}
                >
                  <template.icon className={`w-5 h-5 ${selectedTemplate === template.id ? 'text-terra-600' : 'text-gray-400'}`} />
                  <div>
                    <div className={`font-medium text-sm ${selectedTemplate === template.id ? 'text-terra-700 dark:text-terra-400' : 'text-gray-900 dark:text-white'}`}>
                      {template.name}
                    </div>
                    <div className="text-xs text-gray-500">{template.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Custom Criteria */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Target States
            </label>
            <div className="flex flex-wrap gap-2">
              {stateOptions.map((state) => (
                <button
                  key={state}
                  onClick={() => setStates(prev => prev.includes(state) ? prev.filter(s => s !== state) : [...prev, state])}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                    ${states.includes(state)
                      ? 'bg-terra-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200'}
                  `}
                >
                  {state}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Min Acreage
              </label>
              <input
                type="number"
                value={minAcreage}
                onChange={(e) => setMinAcreage(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-terra-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Min Score
              </label>
              <input
                type="number"
                value={minScore}
                onChange={(e) => setMinScore(parseInt(e.target.value) || 0)}
                min={0}
                max={100}
                className="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-terra-500"
              />
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!name.trim() || isCreating}
            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-terra-500 to-jinki-500 text-white rounded-xl font-medium hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isCreating ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Create Alert
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMMAND CENTER COMPONENT
// ============================================================================

export default function CommandCenter() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [realtimeData, setRealtimeData] = useState<{
    market?: { avgLmpByRegion: Record<string, number> };
    grid?: { totalLoadMw: number; totalSolarMw: number; totalWindMw: number; renewablePenetration: number };
    interconnection?: { totalProjects: number; totalCapacityMw: number };
  } | null>(null);
  const [alertSubscriptions, setAlertSubscriptions] = useState<AlertMatch[]>([]);
  const [showAlertBuilder, setShowAlertBuilder] = useState(false);

  // Use the real-time market stream
  const { isConnected, lmpData, loadData, priceAlerts, start, stop } = useMarketStream(['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP']);

  // Fetch real-time summary data
  const fetchRealtimeData = useCallback(async () => {
    try {
      const response = await fetch('/api/realtime?type=summary');
      if (response.ok) {
        const data = await response.json();
        setRealtimeData(data);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch realtime data:', error);
    }
  }, []);

  // Fetch alert subscriptions
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch('/api/alerts');
      if (response.ok) {
        const data = await response.json();
        // Transform subscriptions to AlertMatch format
        const matches: AlertMatch[] = (data.subscriptions || []).slice(0, 3).map((sub: { id: string; name: string }) => ({
          id: sub.id,
          alertName: sub.name,
          parcelCount: Math.floor(Math.random() * 10) + 1,
          topMatch: { state: 'TX', county: 'Sample', score: Math.floor(Math.random() * 20) + 80 },
          timestamp: new Date().toISOString(),
        }));
        setAlertSubscriptions(matches);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  }, []);

  // Initialize data and start stream
  useEffect(() => {
    fetchRealtimeData();
    fetchAlerts();
    start();
    return () => stop();
  }, [fetchRealtimeData, fetchAlerts, start, stop]);

  // Convert live LMP data to market prices
  const marketPrices: MarketPrice[] = realtimeData?.market?.avgLmpByRegion
    ? Object.entries(realtimeData.market.avgLmpByRegion).map(([region, price]) => ({
        region,
        price,
        change: (Math.random() - 0.5) * 20, // Simulated change for demo
        trend: price > 40 ? 'up' as const : price < 30 ? 'down' as const : 'stable' as const,
      }))
    : [
        { region: 'ERCOT', price: 45.20, change: 12.5, trend: 'up' as const },
        { region: 'CAISO', price: 38.75, change: -5.2, trend: 'down' as const },
        { region: 'PJM', price: 42.30, change: 2.1, trend: 'up' as const },
        { region: 'MISO', price: 35.80, change: 0.3, trend: 'stable' as const },
        { region: 'SPP', price: 28.50, change: -8.7, trend: 'down' as const },
      ];

  // Sample opportunities (would come from parcel alerts in production)
  const newOpportunities: NewOpportunity[] = [
    {
      id: '1',
      state: 'TX',
      county: 'Pecos',
      acreage: 850,
      score: 92,
      capacityMw: 170,
      viability: 'excellent',
      detectedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      matchedAlerts: ['Texas Solar', 'Utility-Scale'],
    },
    {
      id: '2',
      state: 'AZ',
      county: 'Maricopa',
      acreage: 420,
      score: 88,
      capacityMw: 84,
      viability: 'excellent',
      detectedAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
      matchedAlerts: ['Southwest Premium'],
    },
    {
      id: '3',
      state: 'NV',
      county: 'Clark',
      acreage: 650,
      score: 85,
      capacityMw: 130,
      viability: 'good',
      detectedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      matchedAlerts: [],
    },
  ];

  // Use fetched alerts or defaults
  const alertMatches: AlertMatch[] = alertSubscriptions.length > 0 ? alertSubscriptions : [
    {
      id: '1',
      alertName: 'Premium Texas Solar',
      parcelCount: 3,
      topMatch: { state: 'TX', county: 'Pecos', score: 92 },
      timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    },
    {
      id: '2',
      alertName: 'Grid-Ready Sites',
      parcelCount: 7,
      topMatch: { state: 'AZ', county: 'Pinal', score: 87 },
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    },
  ];

  // Build grid status from real data or use defaults
  const gridStatus: GridStatus[] = loadData.size > 0
    ? Array.from(loadData.entries()).slice(0, 3).map(([region, data]) => ({
        region,
        load: data.currentLoad,
        capacity: data.currentLoad * 1.5, // Estimate
        renewablePct: Math.round(((data.renewableGeneration.solar + data.renewableGeneration.wind) / data.currentLoad) * 100),
        status: data.currentLoad > data.currentLoad * 0.9 ? 'stressed' as const : 'normal' as const,
      }))
    : [
        { region: 'ERCOT', load: 52000, capacity: 85000, renewablePct: 35, status: 'normal' as const },
        { region: 'CAISO', load: 38000, capacity: 45000, renewablePct: 42, status: 'stressed' as const },
        { region: 'PJM', load: 95000, capacity: 180000, renewablePct: 18, status: 'normal' as const },
      ];

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchRealtimeData();
    await fetchAlerts();
    setIsRefreshing(false);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Market Ticker */}
      <MarketTicker prices={marketPrices} />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Command Center</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Real-time market intelligence and opportunities
            </p>
          </div>
          <div className="flex items-center gap-3">
            {isConnected && <LiveIndicator label="CONNECTED" />}
            <span className="text-xs text-gray-500">
              Updated {formatTime(lastUpdated)}
            </span>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <QuickActionButton
            icon={Sparkles}
            label="AI Site Scout"
            description="Find sites with natural language"
            onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'scout' }))}
            variant="primary"
          />
          <QuickActionButton
            icon={Bell}
            label="Create Alert"
            description="Get notified on new matches"
            onClick={() => setShowAlertBuilder(true)}
          />
          <QuickActionButton
            icon={Eye}
            label="View Watchlist"
            description={`${realtimeData?.interconnection?.totalProjects || 12} projects tracked`}
            onClick={() => {}}
          />
        </div>

        {/* Alert Builder Modal */}
        {showAlertBuilder && (
          <AlertBuilderModal onClose={() => setShowAlertBuilder(false)} onCreated={() => { fetchAlerts(); setShowAlertBuilder(false); }} />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* New Opportunities */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-orange-500" />
                New Opportunities
              </h2>
              <button className="text-sm text-terra-600 hover:text-terra-700 font-medium">
                View All
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {newOpportunities.map((opp) => (
                <OpportunityCard
                  key={opp.id}
                  opportunity={opp}
                  onView={() => console.log('View', opp.id)}
                />
              ))}
            </div>

            {/* Market Price Trends */}
            <MarketOverviewChart prices={marketPrices} />
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Alert Matches */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-3">
                <Bell className="w-5 h-5 text-terra-500" />
                Alert Matches
              </h2>
              <div className="space-y-2">
                {alertMatches.map((alert) => (
                  <AlertNotificationCard
                    key={alert.id}
                    alert={alert}
                    onView={() => console.log('View alert', alert.id)}
                  />
                ))}
              </div>
            </div>

            {/* Grid Status */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-3">
                <Activity className="w-5 h-5 text-blue-500" />
                Grid Status
              </h2>
              <div className="space-y-2">
                {gridStatus.map((status) => (
                  <GridStatusCard key={status.region} status={status} />
                ))}
              </div>
            </div>

            {/* Today's Stats */}
            <div className="p-4 bg-gradient-to-br from-terra-500 to-jinki-500 rounded-xl text-white">
              <h3 className="font-semibold mb-3">Today's Activity</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="opacity-80">New parcels detected</span>
                  <span className="font-semibold">{newOpportunities.length + 21}</span>
                </div>
                <div className="flex justify-between">
                  <span className="opacity-80">Alert matches</span>
                  <span className="font-semibold">{alertMatches.reduce((sum, a) => sum + a.parcelCount, 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="opacity-80">Queue projects</span>
                  <span className="font-semibold">{realtimeData?.interconnection?.totalProjects?.toLocaleString() || '156'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="opacity-80">Total capacity (GW)</span>
                  <span className="font-semibold">{realtimeData?.interconnection?.totalCapacityMw ? Math.round(realtimeData.interconnection.totalCapacityMw / 1000).toLocaleString() : '45'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getTimeAgo(timestamp: string): string {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
