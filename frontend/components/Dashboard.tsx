'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  TrendingUp,
  MapPin,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
  ChevronRight,
  Play,
  Sun,
  Wind,
  DollarSign,
  BarChart3,
  Globe,
  Target,
} from 'lucide-react';
import { US_PARCELS, getTotalStatistics, getStateStatistics } from '@/lib/us-parcels-data';

interface DashboardProps {
  onSelectParcel: (id: string) => void;
}

export function Dashboard({ onSelectParcel }: DashboardProps) {
  const [stats, setStats] = useState<ReturnType<typeof getTotalStatistics> | null>(null);
  const [stateStats, setStateStats] = useState<ReturnType<typeof getStateStatistics> | null>(null);
  const [topParcels, setTopParcels] = useState<typeof US_PARCELS>([]);

  useEffect(() => {
    setStats(getTotalStatistics());
    setStateStats(getStateStatistics());
    // Get top 10 parcels by score
    const sorted = [...US_PARCELS].sort((a, b) => b.overall_score - a.overall_score);
    setTopParcels(sorted.slice(0, 10));
  }, []);

  const getViabilityColor = (viability: string) => {
    switch (viability) {
      case 'excellent': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'good': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
      case 'moderate': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      default: return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'bg-green-500';
    if (score >= 70) return 'bg-blue-500';
    if (score >= 55) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  // Get top states by parcel count
  const topStates = stateStats
    ? Object.entries(stateStats)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 8)
    : [];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-gray-50 dark:bg-gray-900">
      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Parcels"
          value={stats?.parcelCount.toLocaleString() || '2,000+'}
          subtitle="Across all 50 states"
          icon={MapPin}
          color="bg-terra-500"
          trend="+12% vs last month"
        />
        <StatCard
          title="Total Acreage"
          value={stats ? `${(stats.totalAcreage / 1000).toFixed(0)}K` : '1M+'}
          subtitle="acres available"
          icon={Globe}
          color="bg-blue-500"
          trend="+8% vs last month"
        />
        <StatCard
          title="Solar Capacity"
          value={stats ? `${(stats.totalSolarCapacity / 1000).toFixed(1)}GW` : '200GW'}
          subtitle="potential"
          icon={Sun}
          color="bg-yellow-500"
          trend="+15% vs last month"
        />
        <StatCard
          title="Excellent Sites"
          value={stats?.excellentCount.toLocaleString() || '500+'}
          subtitle="score 85+"
          icon={Target}
          color="bg-green-500"
          trend="+24 new this week"
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MiniStatCard
          label="Average Score"
          value={stats?.avgScore?.toString() || '72'}
          icon={BarChart3}
        />
        <MiniStatCard
          label="Good+ Sites"
          value={stats ? (stats.excellentCount + stats.goodCount).toLocaleString() : '1,200'}
          icon={CheckCircle}
        />
        <MiniStatCard
          label="Wind Capacity"
          value={stats ? `${(stats.totalWindCapacity / 1000).toFixed(1)}GW` : '40GW'}
          icon={Wind}
        />
        <MiniStatCard
          label="States Covered"
          value={stats?.stateCount?.toString() || '50'}
          icon={Globe}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Parcels */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Top Scored Parcels
              </h2>
              <p className="text-sm text-gray-500">Highest potential development sites nationwide</p>
            </div>
            <button className="text-sm text-terra-600 hover:text-terra-700 font-medium">
              View All
            </button>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {topParcels.map((parcel, idx) => (
              <div
                key={parcel.id}
                onClick={() => onSelectParcel(parcel.id)}
                className="px-5 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-sm font-bold text-gray-600 dark:text-gray-300">
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {parcel.county}, {parcel.state}
                    </div>
                    <div className="text-sm text-gray-500 flex items-center gap-3">
                      <span>{parcel.acreage.toLocaleString()} acres</span>
                      <span>•</span>
                      <span>{parcel.solar_permission}</span>
                      <span>•</span>
                      <span>{parcel.nearest_substation_mi} mi to grid</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getViabilityColor(parcel.viability)}`}>
                    {parcel.viability}
                  </span>
                  <div className={`w-10 h-10 rounded-lg ${getScoreColor(parcel.overall_score)} flex items-center justify-center`}>
                    <span className="text-white font-bold">{parcel.overall_score}</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-terra-600 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* State Leaderboard */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Top States
            </h2>
            <p className="text-sm text-gray-500">By number of quality sites</p>
          </div>

          <div className="p-4 space-y-3">
            {topStates.map(([stateCode, data], idx) => (
              <div key={stateCode} className="flex items-center gap-3">
                <div className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${
                  idx === 0 ? 'bg-yellow-400 text-yellow-900' :
                  idx === 1 ? 'bg-gray-300 text-gray-700' :
                  idx === 2 ? 'bg-amber-600 text-white' :
                  'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                }`}>
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900 dark:text-white">{stateCode}</span>
                    <span className="text-sm text-gray-500">{data.count} parcels</span>
                  </div>
                  <div className="mt-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-terra-500 rounded-full"
                      style={{ width: `${(data.count / topStates[0][1].count) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Avg Score: {data.avgScore}</span>
                    <span>{(data.totalCapacity / 1000).toFixed(1)}GW capacity</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Viability Breakdown */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Viability Breakdown</h3>
          <div className="space-y-3">
            {[
              { label: 'Excellent', count: stats?.excellentCount || 0, color: 'bg-green-500' },
              { label: 'Good', count: stats?.goodCount || 0, color: 'bg-blue-500' },
              { label: 'Moderate', count: stats?.moderateCount || 0, color: 'bg-yellow-500' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${item.color}`} />
                <span className="flex-1 text-sm text-gray-600 dark:text-gray-400">{item.label}</span>
                <span className="font-semibold text-gray-900 dark:text-white">{item.count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Resource Mix */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Resource Potential</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                  <Sun className="w-4 h-4 text-yellow-500" /> Solar
                </span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {stats ? `${(stats.totalSolarCapacity / 1000).toFixed(1)}GW` : '200GW'}
                </span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-yellow-500 rounded-full" style={{ width: '85%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                  <Wind className="w-4 h-4 text-blue-500" /> Wind
                </span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {stats ? `${(stats.totalWindCapacity / 1000).toFixed(1)}GW` : '40GW'}
                </span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '35%' }} />
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
          <div className="space-y-2">
            <button className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-terra-500 hover:bg-terra-50 dark:hover:bg-terra-900/20 transition-colors text-left">
              <div className="p-2 bg-terra-100 dark:bg-terra-900/30 rounded-lg">
                <Target className="w-4 h-4 text-terra-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900 dark:text-white text-sm">AI Site Scout</div>
                <div className="text-xs text-gray-500">Find sites with natural language</div>
              </div>
            </button>
            <button className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-left">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <BarChart3 className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900 dark:text-white text-sm">Financial Model</div>
                <div className="text-xs text-gray-500">Calculate IRR, NPV, LCOE</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  trend: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2.5 ${color} rounded-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <span className="text-xs text-green-600 font-medium">{trend}</span>
      </div>
      <div>
        <div className="text-3xl font-bold text-gray-900 dark:text-white">{value}</div>
        <div className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</div>
        <div className="text-xs text-gray-400 mt-1">{title}</div>
      </div>
    </div>
  );
}

function MiniStatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-gray-400" />
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <div className="text-xl font-bold text-gray-900 dark:text-white">{value}</div>
    </div>
  );
}
