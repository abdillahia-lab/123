'use client';

import { useState, useEffect, useRef } from 'react';
import {
  Search,
  Sparkles,
  MapPin,
  Zap,
  TrendingUp,
  ChevronRight,
  Filter,
  Download,
  Star,
  AlertCircle,
  Sun,
  Wind,
  DollarSign,
  Grid,
  CheckCircle,
  Clock,
  BarChart3,
} from 'lucide-react';
import {
  parseNaturalLanguageQuery,
  executeSearch,
  SMART_SEARCHES,
  type SearchResult,
  type EnrichedParcel,
} from '@/lib/ai-site-scout';

interface AISiteScoutProps {
  onSelectParcel: (id: string) => void;
}

export function AISiteScout({ onSelectParcel }: AISiteScoutProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [selectedParcels, setSelectedParcels] = useState<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setShowSuggestions(false);

    // Simulate AI processing delay
    await new Promise(resolve => setTimeout(resolve, 800));

    const parsedQuery = parseNaturalLanguageQuery(searchQuery);
    const searchResults = executeSearch(parsedQuery);

    setResults(searchResults);
    setIsSearching(false);
  };

  const handleSmartSearch = (smartQuery: string) => {
    setQuery(smartQuery);
    handleSearch(smartQuery);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(query);
    }
  };

  const toggleParcelSelection = (id: string) => {
    const newSelection = new Set(selectedParcels);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedParcels(newSelection);
  };

  const getViabilityColor = (viability: string) => {
    switch (viability) {
      case 'excellent': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'good': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
      case 'moderate': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'challenging': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
      default: return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
    }
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-green-500 text-white';
      case 'B': return 'bg-blue-500 text-white';
      case 'C': return 'bg-yellow-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Search Header */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-gradient-to-br from-terra-500 to-jinki-500 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">AI Site Scout</h2>
              <p className="text-sm text-gray-500">Search with natural language to find the perfect sites</p>
            </div>
          </div>

          {/* Search Input */}
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => !results && setShowSuggestions(true)}
              placeholder="Try: 'Show me 500+ acre solar sites in Texas with by-right permitting'"
              className="w-full px-5 py-4 pl-12 pr-32 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-terra-500 focus:border-transparent"
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <button
              onClick={() => handleSearch(query)}
              disabled={isSearching || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-terra-600 text-white rounded-lg font-medium hover:bg-terra-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSearching ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Search
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          {/* Smart Search Suggestions */}
          {showSuggestions && !results && (
            <div className="mb-8">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                Smart Searches
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {SMART_SEARCHES.map((search, i) => (
                  <button
                    key={i}
                    onClick={() => handleSmartSearch(search.query)}
                    className="flex items-center gap-3 p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-terra-500 hover:shadow-md transition-all text-left group"
                  >
                    <div className="p-2 bg-terra-100 dark:bg-terra-900/30 rounded-lg group-hover:bg-terra-500 transition-colors">
                      <Sparkles className="w-4 h-4 text-terra-600 group-hover:text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 dark:text-white">{search.name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{search.query}</div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-terra-600" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <SummaryCard
                  label="Sites Found"
                  value={results.totalCount.toString()}
                  icon={MapPin}
                  color="terra"
                />
                <SummaryCard
                  label="Total Acreage"
                  value={results.summary.totalAcreage.toLocaleString()}
                  icon={Grid}
                  color="blue"
                />
                <SummaryCard
                  label="Total Capacity"
                  value={`${results.summary.totalCapacityMW.toLocaleString()} MW`}
                  icon={Zap}
                  color="yellow"
                />
                <SummaryCard
                  label="Avg Score"
                  value={results.summary.avgScore.toString()}
                  icon={BarChart3}
                  color="green"
                />
              </div>

              {/* Suggestions */}
              {results.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {results.suggestions.map((suggestion, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full text-sm"
                    >
                      <AlertCircle className="w-3.5 h-3.5" />
                      {suggestion}
                    </div>
                  ))}
                </div>
              )}

              {/* Action Bar */}
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Showing {results.parcels.length} of {results.totalCount} parcels
                  {selectedParcels.size > 0 && (
                    <span className="ml-2 text-terra-600">• {selectedParcels.size} selected</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
                    <Filter className="w-4 h-4" />
                    Refine
                  </button>
                  <button className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                </div>
              </div>

              {/* Results Grid */}
              <div className="space-y-3">
                {results.parcels.map((parcel) => (
                  <ParcelCard
                    key={parcel.id}
                    parcel={parcel}
                    isSelected={selectedParcels.has(parcel.id)}
                    onSelect={() => toggleParcelSelection(parcel.id)}
                    onClick={() => onSelectParcel(parcel.id)}
                    getViabilityColor={getViabilityColor}
                    getGradeColor={getGradeColor}
                  />
                ))}
              </div>

              {results.parcels.length === 0 && (
                <div className="text-center py-12">
                  <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No parcels found</h3>
                  <p className="text-gray-500">Try adjusting your search criteria</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'terra' | 'blue' | 'yellow' | 'green';
}) {
  const colorClasses = {
    terra: 'bg-terra-100 text-terra-600 dark:bg-terra-900/30 dark:text-terra-400',
    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
    green: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1.5 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
    </div>
  );
}

function ParcelCard({
  parcel,
  isSelected,
  onSelect,
  onClick,
  getViabilityColor,
  getGradeColor,
}: {
  parcel: EnrichedParcel;
  isSelected: boolean;
  onSelect: () => void;
  onClick: () => void;
  getViabilityColor: (v: string) => string;
  getGradeColor: (g: string) => string;
}) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl border-2 transition-all ${
        isSelected
          ? 'border-terra-500 shadow-md'
          : 'border-gray-200 dark:border-gray-700 hover:border-terra-300'
      }`}
    >
      <div className="p-4">
        <div className="flex items-start gap-4">
          {/* Rank & Selection */}
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-sm font-bold text-gray-600 dark:text-gray-300">
              #{parcel.rank}
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); onSelect(); }}
              className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
                isSelected
                  ? 'bg-terra-500 border-terra-500'
                  : 'border-gray-300 dark:border-gray-600 hover:border-terra-500'
              }`}
            >
              {isSelected && <CheckCircle className="w-4 h-4 text-white" />}
            </button>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white">
                  {parcel.county}, {parcel.state}
                </h4>
                <p className="text-sm text-gray-500">{parcel.address}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getGradeColor(parcel.investmentGrade)}`}>
                  Grade {parcel.investmentGrade}
                </span>
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-terra-500 to-jinki-500 flex items-center justify-center">
                  <span className="text-xl font-bold text-white">{parcel.overall_score}</span>
                </div>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              <MetricItem icon={Grid} label="Acreage" value={`${parcel.acreage.toLocaleString()} ac`} />
              <MetricItem icon={Zap} label="Capacity" value={`${parcel.estimatedCapacityMW} MW`} />
              <MetricItem icon={Sun} label="Solar GHI" value={`${parcel.solar_ghi} kWh/m²/d`} />
              <MetricItem icon={Wind} label="Wind" value={`${parcel.wind_speed} m/s`} />
            </div>

            {/* Additional Info */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getViabilityColor(parcel.viability)}`}>
                {parcel.viability}
              </span>
              <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-300">
                {parcel.solar_permission}
              </span>
              <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-300">
                {parcel.zoning_type}
              </span>
              <span className="text-xs text-gray-500">
                {parcel.nearest_substation_mi} mi to substation • {parcel.transmission_voltage_kv}kV
              </span>
            </div>

            {/* Highlights */}
            {parcel.highlights.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {parcel.highlights.map((highlight, i) => (
                  <span key={i} className="flex items-center gap-1 px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded text-xs">
                    <Star className="w-3 h-3" />
                    {highlight}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Financial Summary */}
          <div className="hidden lg:block w-48 pl-4 border-l border-gray-200 dark:border-gray-700">
            <div className="space-y-2">
              <div>
                <div className="text-xs text-gray-500">Est. CAPEX</div>
                <div className="font-semibold text-gray-900 dark:text-white">
                  ${(parcel.estimatedCapex / 1000000).toFixed(1)}M
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Est. Annual Revenue</div>
                <div className="font-semibold text-gray-900 dark:text-white">
                  ${(parcel.estimatedAnnualRevenue / 1000000).toFixed(2)}M
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Est. IRR</div>
                <div className="font-semibold text-green-600">{parcel.estimatedIRR}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Land Cost</div>
                <div className="font-semibold text-gray-900 dark:text-white">
                  ${parcel.estimated_land_cost_per_acre.toLocaleString()}/ac
                </div>
              </div>
            </div>
          </div>

          {/* Action */}
          <button
            onClick={onClick}
            className="self-center p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
    </div>
  );
}

function MetricItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4 text-gray-400" />
      <div>
        <div className="text-xs text-gray-500">{label}</div>
        <div className="text-sm font-medium text-gray-900 dark:text-white">{value}</div>
      </div>
    </div>
  );
}
