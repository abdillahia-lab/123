'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, type Analysis } from '@/lib/api';
import {
  X,
  MapPin,
  FileText,
  Zap,
  Leaf,
  Grid3X3,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Play,
  Download,
} from 'lucide-react';
import { ScoreRing } from './ScoreRing';
import { motion, AnimatePresence } from 'framer-motion';

interface AnalysisPanelProps {
  parcelId: string;
  onClose: () => void;
}

export function AnalysisPanel({ parcelId, onClose }: AnalysisPanelProps) {
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [expandedSection, setExpandedSection] = useState<string | null>('overview');

  const { data: parcel } = useQuery({
    queryKey: ['parcel', parcelId],
    queryFn: () => api.getParcel(parcelId),
  });

  const analyzeMutation = useMutation({
    mutationFn: () => api.analyzeSite(parcelId),
  });

  const handleAnalyze = () => {
    setAnalyzing(true);
    setProgress(0);

    // Simulate progress (in real app, use WebSocket)
    const steps = [
      'Planning analysis...',
      'Analyzing permitting...',
      'Checking grid connection...',
      'Screening environmental...',
      'Evaluating land...',
      'Calculating scores...',
      'Generating recommendations...',
    ];

    let stepIndex = 0;
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        setCurrentStep(steps[stepIndex]);
        setProgress((stepIndex + 1) / steps.length);
        stepIndex++;
      } else {
        clearInterval(interval);
        analyzeMutation.mutate();
      }
    }, 500);

    analyzeMutation.mutate();
  };

  const analysis = analyzeMutation.data;

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h2 className="font-semibold text-gray-900 dark:text-white">
          Site Analysis
        </h2>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Parcel info */}
        {parcel && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-terra-100 dark:bg-terra-900/30 rounded-lg">
                <MapPin className="w-5 h-5 text-terra-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {parcel.county}, {parcel.state}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {parcel.acreage} acres • {parcel.zoning_type}
                </p>
                {parcel.owner_name && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Owner: {parcel.owner_name}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Analysis results or start button */}
        {!analysis && !analyzing ? (
          <div className="p-4">
            <button
              onClick={handleAnalyze}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-terra-600 to-jinki-600 text-white font-medium rounded-lg hover:from-terra-700 hover:to-jinki-700 transition-all"
            >
              <Play className="w-5 h-5" />
              Start Analysis
            </button>
            <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">
              Comprehensive AI analysis in ~60 seconds
            </p>
          </div>
        ) : analyzing && !analysis ? (
          <div className="p-4">
            <div className="text-center">
              <div className="relative inline-flex">
                <ScoreRing score={progress * 100} size={120} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {Math.round(progress * 100)}%
                  </span>
                </div>
              </div>
              <p className="mt-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                {currentStep}
              </p>
            </div>
          </div>
        ) : analysis ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {/* Overall score */}
            <div className="p-4">
              <div className="flex items-center gap-4">
                <ScoreRing score={analysis.overall_score} size={80} />
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {analysis.overall_score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                    {analysis.viability} Viability
                  </div>
                </div>
              </div>
            </div>

            {/* Score breakdown */}
            <CollapsibleSection
              title="Score Breakdown"
              icon={Grid3X3}
              isOpen={expandedSection === 'breakdown'}
              onToggle={() =>
                setExpandedSection(
                  expandedSection === 'breakdown' ? null : 'breakdown'
                )
              }
            >
              <div className="space-y-3">
                <ScoreBar
                  label="Permitting"
                  score={analysis.permitting_score}
                  color="bg-purple-500"
                />
                <ScoreBar
                  label="Grid"
                  score={analysis.grid_score}
                  color="bg-blue-500"
                />
                <ScoreBar
                  label="Environmental"
                  score={analysis.environmental_score}
                  color="bg-green-500"
                />
                <ScoreBar
                  label="Land"
                  score={analysis.land_score}
                  color="bg-yellow-500"
                />
              </div>
            </CollapsibleSection>

            {/* Fatal flaws */}
            {analysis.fatal_flaws.length > 0 && (
              <CollapsibleSection
                title={`Fatal Flaws (${analysis.fatal_flaws.length})`}
                icon={AlertTriangle}
                isOpen={expandedSection === 'flaws'}
                onToggle={() =>
                  setExpandedSection(expandedSection === 'flaws' ? null : 'flaws')
                }
              >
                <div className="space-y-2">
                  {analysis.fatal_flaws.map((flaw, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg"
                    >
                      <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-red-700 dark:text-red-400">
                        {flaw}
                      </span>
                    </div>
                  ))}
                </div>
              </CollapsibleSection>
            )}

            {/* Recommendations */}
            <CollapsibleSection
              title="Recommendations"
              icon={CheckCircle}
              isOpen={expandedSection === 'recommendations'}
              onToggle={() =>
                setExpandedSection(
                  expandedSection === 'recommendations' ? null : 'recommendations'
                )
              }
            >
              <div className="space-y-2">
                {analysis.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                  >
                    <span className="flex items-center justify-center w-5 h-5 bg-terra-100 dark:bg-terra-900/30 rounded-full text-xs font-medium text-terra-700 dark:text-terra-400 flex-shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {rec}
                    </span>
                  </div>
                ))}
              </div>
            </CollapsibleSection>

            {/* Analysis info */}
            <div className="p-4">
              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>
                    Completed in {analysis.duration_seconds.toFixed(1)}s
                  </span>
                </div>
                <button className="flex items-center gap-1 text-terra-600 hover:text-terra-700">
                  <Download className="w-4 h-4" />
                  Export
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function CollapsibleSection({
  title,
  icon: Icon,
  children,
  isOpen,
  onToggle,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-gray-500" />
          <span className="font-medium text-gray-900 dark:text-white">
            {title}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ScoreBar({
  label,
  score,
  color,
}: {
  label: string;
  score: number;
  color: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
        <span className="text-sm font-medium text-gray-900 dark:text-white">
          {score.toFixed(1)}
        </span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${color} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.5, delay: 0.1 }}
        />
      </div>
    </div>
  );
}
