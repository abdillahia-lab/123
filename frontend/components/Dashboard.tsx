'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api, type Parcel, type Analysis } from '@/lib/api';
import {
  TrendingUp,
  MapPin,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
} from 'lucide-react';
import { ScoreRing } from './ScoreRing';

interface DashboardProps {
  onSelectParcel: (id: string) => void;
}

export function Dashboard({ onSelectParcel }: DashboardProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.stats(),
  });

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  });

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Parcels"
          value={stats?.parcels_count || 0}
          icon={MapPin}
          color="bg-terra-500"
          trend="+12%"
        />
        <StatCard
          title="Active Projects"
          value={stats?.projects_count || 0}
          icon={Zap}
          color="bg-jinki-500"
          trend="+5%"
        />
        <StatCard
          title="Analyses Run"
          value={stats?.analyses_count || 0}
          icon={TrendingUp}
          color="bg-blue-500"
          trend="+28%"
        />
        <StatCard
          title="High-Value Sites"
          value={0}
          icon={CheckCircle}
          color="bg-green-500"
          trend="+3"
        />
      </div>

      {/* Quick actions */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-3 p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-terra-500 hover:bg-terra-50 dark:hover:bg-terra-900/20 transition-colors"
          >
            <div className="p-2 bg-terra-100 dark:bg-terra-900/30 rounded-lg">
              <Plus className="w-5 h-5 text-terra-600" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900 dark:text-white">
                Add Parcel
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Register a new site
              </div>
            </div>
          </button>

          <button className="flex items-center gap-3 p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-jinki-500 hover:bg-jinki-50 dark:hover:bg-jinki-900/20 transition-colors">
            <div className="p-2 bg-jinki-100 dark:bg-jinki-900/30 rounded-lg">
              <Zap className="w-5 h-5 text-jinki-600" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900 dark:text-white">
                Quick Analysis
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Score a parcel instantly
              </div>
            </div>
          </button>

          <button className="flex items-center gap-3 p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <MapPin className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900 dark:text-white">
                Explore Map
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Find sites visually
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Recent projects */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Projects
          </h2>
          <button className="text-sm text-terra-600 hover:text-terra-700 font-medium">
            View All
          </button>
        </div>

        {projects && projects.length > 0 ? (
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => (
              <ProjectRow key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FolderIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No projects yet</p>
            <p className="text-sm">Create your first project to get started</p>
          </div>
        )}
      </div>

      {/* Create Parcel Modal */}
      {showCreateModal && (
        <CreateParcelModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  trend,
}: {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  trend: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div className={`p-2 ${color} rounded-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm text-green-600 font-medium">{trend}</span>
      </div>
      <div className="mt-4">
        <div className="text-2xl font-bold text-gray-900 dark:text-white">
          {value.toLocaleString()}
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">{title}</div>
      </div>
    </div>
  );
}

function ProjectRow({ project }: { project: any }) {
  const stageColors: Record<string, string> = {
    prospecting: 'bg-gray-100 text-gray-700',
    due_diligence: 'bg-yellow-100 text-yellow-700',
    site_control: 'bg-blue-100 text-blue-700',
    permitting: 'bg-purple-100 text-purple-700',
    construction: 'bg-green-100 text-green-700',
  };

  return (
    <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-terra-500 to-jinki-500 rounded-lg flex items-center justify-center">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="font-medium text-gray-900 dark:text-white">
            {project.name}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {project.total_acreage} acres • {project.capacity_mw} MW
          </div>
        </div>
      </div>
      <span
        className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
          stageColors[project.stage] || stageColors.prospecting
        }`}
      >
        {project.stage.replace('_', ' ')}
      </span>
    </div>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
      />
    </svg>
  );
}

function CreateParcelModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState({
    state: '',
    county: '',
    acreage: '',
    municipality: '',
    owner_name: '',
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createParcel(data),
    onSuccess: () => {
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      ...formData,
      acreage: parseFloat(formData.acreage),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Add New Parcel
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                State
              </label>
              <input
                type="text"
                value={formData.state}
                onChange={(e) =>
                  setFormData({ ...formData, state: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="TX"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                County
              </label>
              <input
                type="text"
                value={formData.county}
                onChange={(e) =>
                  setFormData({ ...formData, county: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Harris"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Acreage
            </label>
            <input
              type="number"
              value={formData.acreage}
              onChange={(e) =>
                setFormData({ ...formData, acreage: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Municipality (optional)
            </label>
            <input
              type="text"
              value={formData.municipality}
              onChange={(e) =>
                setFormData({ ...formData, municipality: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Houston"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Owner Name (optional)
            </label>
            <input
              type="text"
              value={formData.owner_name}
              onChange={(e) =>
                setFormData({ ...formData, owner_name: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="John Smith"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 px-4 py-2 bg-terra-600 text-white rounded-lg hover:bg-terra-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Parcel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
