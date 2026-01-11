'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Map,
  FolderKanban,
  Search,
  Settings,
  ChevronLeft,
  Zap,
  Sun,
  Wind,
  Battery,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Site Explorer', href: '/explorer', icon: Map },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Search', href: '/search', icon: Search },
];

const projectTypes = [
  { name: 'Solar', icon: Sun, color: 'text-yellow-500' },
  { name: 'Wind', icon: Wind, color: 'text-blue-500' },
  { name: 'Storage', icon: Battery, color: 'text-green-500' },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <aside
      className={`${
        collapsed ? 'w-16' : 'w-64'
      } bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col transition-all duration-300`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-terra-500 to-jinki-500 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900 dark:text-white">
              TerraJinki
            </span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <ChevronLeft
            className={`w-5 h-5 text-gray-500 transition-transform ${
              collapsed ? 'rotate-180' : ''
            }`}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive
                  ? 'bg-terra-50 text-terra-700 dark:bg-terra-900/20 dark:text-terra-400'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="font-medium">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Project types */}
      {!collapsed && (
        <div className="px-4 py-4 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Project Types
          </h3>
          <div className="space-y-2">
            {projectTypes.map((type) => (
              <div
                key={type.name}
                className="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 dark:text-gray-300"
              >
                <type.icon className={`w-4 h-4 ${type.color}`} />
                <span>{type.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings */}
      <div className="px-2 py-4 border-t border-gray-200 dark:border-gray-700">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="font-medium">Settings</span>}
        </Link>
      </div>
    </aside>
  );
}
