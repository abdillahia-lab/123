'use client';

import { useState, useMemo } from 'react';
import {
  Calculator,
  TrendingUp,
  DollarSign,
  Percent,
  Clock,
  BarChart3,
  PieChart,
  RefreshCw,
  Download,
  Sun,
  Wind,
  ChevronDown,
  ChevronUp,
  Info,
  Zap,
} from 'lucide-react';
import {
  getDefaultSolarAssumptions,
  getDefaultWindAssumptions,
  calculateFinancials,
  runSensitivityAnalysis,
  type ProjectAssumptions,
  type FinancialResults,
  type SensitivityResult,
} from '@/lib/financial-model';

export function FinancialModeler() {
  const [projectType, setProjectType] = useState<'solar' | 'wind'>('solar');
  const [capacityMW, setCapacityMW] = useState(100);
  const [assumptions, setAssumptions] = useState<ProjectAssumptions>(getDefaultSolarAssumptions(100));
  const [results, setResults] = useState<FinancialResults | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResult[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleProjectTypeChange = (type: 'solar' | 'wind') => {
    setProjectType(type);
    const newAssumptions = type === 'solar'
      ? getDefaultSolarAssumptions(capacityMW)
      : getDefaultWindAssumptions(capacityMW);
    setAssumptions(newAssumptions);
    setResults(null);
  };

  const handleCapacityChange = (newCapacity: number) => {
    setCapacityMW(newCapacity);
    setAssumptions(prev => ({
      ...prev,
      capacityMW: newCapacity,
      interconnectionCost: newCapacity * (projectType === 'solar' ? 50000 : 60000),
      landCostTotal: newCapacity * (projectType === 'solar' ? 5 : 50) * (projectType === 'solar' ? 3000 : 500),
      developmentCost: newCapacity * (projectType === 'solar' ? 25000 : 35000),
    }));
  };

  const handleCalculate = async () => {
    setIsCalculating(true);
    await new Promise(resolve => setTimeout(resolve, 500));

    const financialResults = calculateFinancials(assumptions);
    const sensitivityResults = runSensitivityAnalysis(assumptions);

    setResults(financialResults);
    setSensitivity(sensitivityResults);
    setIsCalculating(false);
  };

  const updateAssumption = <K extends keyof ProjectAssumptions>(
    key: K,
    value: ProjectAssumptions[K]
  ) => {
    setAssumptions(prev => ({ ...prev, [key]: value }));
    setResults(null);
  };

  const formatCurrency = (value: number, decimals: number = 0) => {
    if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
    if (value >= 1000000) return `$${(value / 1000000).toFixed(decimals)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value.toFixed(decimals)}`;
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg">
              <Calculator className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Financial Modeler</h2>
              <p className="text-sm text-gray-500">IRR, NPV, LCOE, and sensitivity analysis</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCalculate}
              disabled={isCalculating}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
            >
              {isCalculating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Calculator className="w-4 h-4" />
              )}
              {isCalculating ? 'Calculating...' : 'Calculate'}
            </button>
            {results && (
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                <Download className="w-4 h-4" />
                Export
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Panel */}
          <div className="lg:col-span-1 space-y-6">
            {/* Project Type */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Project Type</h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleProjectTypeChange('solar')}
                  className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-colors ${
                    projectType === 'solar'
                      ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-yellow-300'
                  }`}
                >
                  <Sun className={`w-5 h-5 ${projectType === 'solar' ? 'text-yellow-600' : 'text-gray-400'}`} />
                  <span className={`font-medium ${projectType === 'solar' ? 'text-yellow-700 dark:text-yellow-400' : 'text-gray-600 dark:text-gray-400'}`}>
                    Solar
                  </span>
                </button>
                <button
                  onClick={() => handleProjectTypeChange('wind')}
                  className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-colors ${
                    projectType === 'wind'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
                  }`}
                >
                  <Wind className={`w-5 h-5 ${projectType === 'wind' ? 'text-blue-600' : 'text-gray-400'}`} />
                  <span className={`font-medium ${projectType === 'wind' ? 'text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}`}>
                    Wind
                  </span>
                </button>
              </div>
            </div>

            {/* Basic Parameters */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Project Parameters</h3>
              <div className="space-y-4">
                <InputField
                  label="Capacity (MW)"
                  value={capacityMW}
                  onChange={(v) => handleCapacityChange(Number(v))}
                  suffix="MW"
                />
                <InputField
                  label="Capacity Factor"
                  value={assumptions.capacityFactorPct}
                  onChange={(v) => updateAssumption('capacityFactorPct', Number(v))}
                  suffix="%"
                />
                <InputField
                  label="Project Life"
                  value={assumptions.projectLifeYears}
                  onChange={(v) => updateAssumption('projectLifeYears', Number(v))}
                  suffix="years"
                />
                <InputField
                  label="Degradation Rate"
                  value={assumptions.degradationPctPerYear}
                  onChange={(v) => updateAssumption('degradationPctPerYear', Number(v))}
                  suffix="%/yr"
                  step={0.1}
                />
              </div>
            </div>

            {/* Revenue */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Revenue</h3>
              <div className="space-y-4">
                <InputField
                  label="PPA Rate"
                  value={assumptions.ppaRatePerMwh}
                  onChange={(v) => updateAssumption('ppaRatePerMwh', Number(v))}
                  prefix="$"
                  suffix="/MWh"
                />
                <InputField
                  label="PPA Escalation"
                  value={assumptions.ppaEscalationPct}
                  onChange={(v) => updateAssumption('ppaEscalationPct', Number(v))}
                  suffix="%/yr"
                  step={0.1}
                />
              </div>
            </div>

            {/* Tax Incentives */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Tax Incentives</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Use PTC instead of ITC</span>
                  <button
                    onClick={() => updateAssumption('usePTC', !assumptions.usePTC)}
                    className={`relative w-11 h-6 rounded-full transition-colors ${
                      assumptions.usePTC ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      assumptions.usePTC ? 'left-6' : 'left-1'
                    }`} />
                  </button>
                </div>
                {!assumptions.usePTC && (
                  <InputField
                    label="ITC Rate"
                    value={assumptions.itcPct}
                    onChange={(v) => updateAssumption('itcPct', Number(v))}
                    suffix="%"
                  />
                )}
                {assumptions.usePTC && (
                  <InputField
                    label="PTC Rate"
                    value={assumptions.ptcPerMwh}
                    onChange={(v) => updateAssumption('ptcPerMwh', Number(v))}
                    prefix="$"
                    suffix="/MWh"
                    step={0.1}
                  />
                )}
                <div className="space-y-2">
                  <CheckboxField
                    label="Domestic Content Bonus (+10%)"
                    checked={assumptions.domesticContentBonus}
                    onChange={(v) => updateAssumption('domesticContentBonus', v)}
                  />
                  <CheckboxField
                    label="Energy Community Bonus (+10%)"
                    checked={assumptions.energyCommunityBonus}
                    onChange={(v) => updateAssumption('energyCommunityBonus', v)}
                  />
                  <CheckboxField
                    label="Low-Income Bonus (+10-20%)"
                    checked={assumptions.lowIncomeBonus}
                    onChange={(v) => updateAssumption('lowIncomeBonus', v)}
                  />
                </div>
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <h3 className="font-semibold text-gray-900 dark:text-white">Advanced Settings</h3>
                {showAdvanced ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
              {showAdvanced && (
                <div className="p-5 pt-0 space-y-4 border-t border-gray-200 dark:border-gray-700">
                  <InputField
                    label="CAPEX"
                    value={assumptions.capexPerWatt}
                    onChange={(v) => updateAssumption('capexPerWatt', Number(v))}
                    prefix="$"
                    suffix="/W"
                    step={0.01}
                  />
                  <InputField
                    label="O&M Cost"
                    value={assumptions.opexPerKwYear}
                    onChange={(v) => updateAssumption('opexPerKwYear', Number(v))}
                    prefix="$"
                    suffix="/kW/yr"
                    step={0.1}
                  />
                  <InputField
                    label="Debt Ratio"
                    value={assumptions.debtPct}
                    onChange={(v) => updateAssumption('debtPct', Number(v))}
                    suffix="%"
                  />
                  <InputField
                    label="Interest Rate"
                    value={assumptions.debtInterestRate}
                    onChange={(v) => updateAssumption('debtInterestRate', Number(v))}
                    suffix="%"
                    step={0.1}
                  />
                  <InputField
                    label="Debt Term"
                    value={assumptions.debtTermYears}
                    onChange={(v) => updateAssumption('debtTermYears', Number(v))}
                    suffix="years"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {!results ? (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-12 border border-gray-200 dark:border-gray-700 text-center">
                <Calculator className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Enter parameters and calculate
                </h3>
                <p className="text-gray-500">
                  Adjust project parameters on the left, then click Calculate to see results
                </p>
              </div>
            ) : (
              <>
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard
                    label="Equity IRR"
                    value={`${results.equityIRR}%`}
                    icon={TrendingUp}
                    color={results.equityIRR >= 12 ? 'green' : results.equityIRR >= 8 ? 'yellow' : 'red'}
                  />
                  <MetricCard
                    label="Project IRR"
                    value={`${results.projectIRR}%`}
                    icon={BarChart3}
                    color="blue"
                  />
                  <MetricCard
                    label="NPV"
                    value={formatCurrency(results.npv, 1)}
                    icon={DollarSign}
                    color={results.npv > 0 ? 'green' : 'red'}
                  />
                  <MetricCard
                    label="LCOE"
                    value={`$${results.lcoe}/MWh`}
                    icon={Zap}
                    color="purple"
                  />
                </div>

                {/* Secondary Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <SecondaryMetric label="Payback Period" value={`${results.paybackYears} years`} />
                  <SecondaryMetric label="DSCR" value={results.debtServiceCoverageRatio.toFixed(2)} />
                  <SecondaryMetric label="Total CAPEX" value={formatCurrency(results.totalCapex)} />
                  <SecondaryMetric label="Total Revenue" value={formatCurrency(results.totalRevenue)} />
                </div>

                {/* Cash Flow Summary */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Cash Flow Summary</h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div>
                      <div className="text-sm text-gray-500">Total Revenue</div>
                      <div className="text-lg font-semibold text-green-600">{formatCurrency(results.totalRevenue)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Total O&M</div>
                      <div className="text-lg font-semibold text-red-600">({formatCurrency(results.totalOpex)})</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Debt Service</div>
                      <div className="text-lg font-semibold text-red-600">({formatCurrency(results.totalDebtService)})</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Tax Benefits</div>
                      <div className="text-lg font-semibold text-green-600">{formatCurrency(results.totalTaxBenefit)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Net Cash Flow</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(results.netCashFlow)}</div>
                    </div>
                  </div>
                </div>

                {/* Sensitivity Analysis */}
                {sensitivity.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Sensitivity Analysis</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-gray-200 dark:border-gray-700">
                            <th className="text-left py-2 text-sm font-medium text-gray-500">Variable</th>
                            <th className="text-center py-2 text-sm font-medium text-gray-500">Low Case</th>
                            <th className="text-center py-2 text-sm font-medium text-gray-500">Base Case</th>
                            <th className="text-center py-2 text-sm font-medium text-gray-500">High Case</th>
                            <th className="text-right py-2 text-sm font-medium text-gray-500">IRR Range</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sensitivity.map((row, i) => (
                            <tr key={i} className="border-b border-gray-100 dark:border-gray-700">
                              <td className="py-3 font-medium text-gray-900 dark:text-white">{row.variable}</td>
                              <td className="py-3 text-center text-gray-600 dark:text-gray-400">
                                {typeof row.lowCase === 'number' && row.lowCase < 1 ? row.lowCase.toFixed(2) : row.lowCase.toFixed(0)}
                              </td>
                              <td className="py-3 text-center text-gray-900 dark:text-white font-medium">
                                {typeof row.baseCase === 'number' && row.baseCase < 1 ? row.baseCase.toFixed(2) : row.baseCase.toFixed(0)}
                              </td>
                              <td className="py-3 text-center text-gray-600 dark:text-gray-400">
                                {typeof row.highCase === 'number' && row.highCase < 1 ? row.highCase.toFixed(2) : row.highCase.toFixed(0)}
                              </td>
                              <td className="py-3 text-right">
                                <span className="text-red-600">{row.irrLow.toFixed(1)}%</span>
                                <span className="mx-2 text-gray-400">→</span>
                                <span className="text-green-600">{row.irrHigh.toFixed(1)}%</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Annual Cash Flows (First 10 Years) */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Annual Cash Flows (First 10 Years)</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left py-2 font-medium text-gray-500">Year</th>
                          <th className="text-right py-2 font-medium text-gray-500">Revenue</th>
                          <th className="text-right py-2 font-medium text-gray-500">O&M</th>
                          <th className="text-right py-2 font-medium text-gray-500">Debt Service</th>
                          <th className="text-right py-2 font-medium text-gray-500">Tax Benefit</th>
                          <th className="text-right py-2 font-medium text-gray-500">Net CF</th>
                          <th className="text-right py-2 font-medium text-gray-500">Cumulative</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.annualCashFlows.slice(0, 10).map((cf) => (
                          <tr key={cf.year} className="border-b border-gray-100 dark:border-gray-700">
                            <td className="py-2 font-medium text-gray-900 dark:text-white">{cf.year}</td>
                            <td className="py-2 text-right text-green-600">{formatCurrency(cf.revenue, 1)}</td>
                            <td className="py-2 text-right text-red-600">({formatCurrency(cf.opex, 1)})</td>
                            <td className="py-2 text-right text-red-600">({formatCurrency(cf.debtService, 1)})</td>
                            <td className="py-2 text-right text-green-600">{formatCurrency(cf.taxBenefit, 1)}</td>
                            <td className="py-2 text-right font-medium text-gray-900 dark:text-white">{formatCurrency(cf.netCashFlow, 1)}</td>
                            <td className={`py-2 text-right font-medium ${cf.cumulativeCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(cf.cumulativeCashFlow, 1)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  prefix,
  suffix,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (value: string) => void;
  prefix?: string;
  suffix?: string;
  step?: number;
}) {
  return (
    <div>
      <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">{label}</label>
      <div className="flex items-center gap-2">
        {prefix && <span className="text-gray-500">{prefix}</span>}
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          step={step}
          className="flex-1 px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        {suffix && <span className="text-gray-500 text-sm">{suffix}</span>}
      </div>
    </div>
  );
}

function CheckboxField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
      />
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
    </label>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'green' | 'red' | 'blue' | 'yellow' | 'purple';
}) {
  const colorClasses = {
    green: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
    red: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
    purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1.5 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
    </div>
  );
}

function SecondaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-lg font-semibold text-gray-900 dark:text-white">{value}</div>
    </div>
  );
}
