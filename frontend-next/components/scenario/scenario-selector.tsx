'use client';

import React, { useState } from 'react';
import { ChevronDown, Check, Briefcase, Building, Settings } from 'lucide-react';
import { useScenario } from '@/contexts/scenario-context';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 场景图标映射
const ScenarioIcons = {
  tender: Building,
  enterprise: Briefcase,
  default: Settings,
};

interface ScenarioSelectorProps {
  className?: string;
  showLabel?: boolean;
  variant?: 'dropdown' | 'card' | 'minimal';
}

export default function ScenarioSelector({
  className = '',
  showLabel = true,
  variant = 'dropdown'
}: ScenarioSelectorProps) {
  const { state, switchScenario } = useScenario();
  const [isOpen, setIsOpen] = useState(false);

  const handleScenarioChange = (scenarioId: string) => {
    switchScenario(scenarioId);
    setIsOpen(false);
  };

  const getScenarioIcon = (scenarioId: string) => {
    const IconComponent = ScenarioIcons[scenarioId as keyof typeof ScenarioIcons] || ScenarioIcons.default;
    return IconComponent;
  };

  const getThemeClasses = (scenarioId: string) => {
    const scenario = state.availableScenarios.find(s => s.id === scenarioId);
    if (!scenario || !scenario.theme || !scenario.theme.primaryColor) {
      return 'text-gray-600 bg-gray-50 border-gray-200';
    }

    switch (scenario.theme.primaryColor) {
      case 'blue':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'green':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'purple':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'orange':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (state.loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-10 w-32 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className={`text-red-500 text-sm ${className}`}>
        场景加载失败
      </div>
    );
  }

  // 卡片变体
  if (variant === 'card') {
    return (
      <div className={`grid gap-4 ${className}`}>
        {showLabel && (
          <h3 className="text-lg font-semibold text-gray-800">选择场景</h3>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {state.availableScenarios.map((scenario) => {
            const Icon = getScenarioIcon(scenario.id);
            const isActive = state.currentScenario?.id === scenario.id;
            const themeClasses = getThemeClasses(scenario.id);

            return (
              <Card
                key={scenario.id}
                className={`p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${
                  isActive
                    ? `ring-2 ring-offset-2 ${themeClasses}`
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleScenarioChange(scenario.id)}
              >
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-lg ${
                    isActive ? themeClasses : 'bg-gray-100 text-gray-600'
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">
                        {scenario.name}
                      </h4>
                      {isActive && (
                        <Check className="h-4 w-4 text-green-600" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {scenario.description}
                    </p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  // 最小化变体
  if (variant === 'minimal') {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        {state.availableScenarios.map((scenario) => {
          const Icon = getScenarioIcon(scenario.id);
          const isActive = state.currentScenario?.id === scenario.id;
          const themeClasses = getThemeClasses(scenario.id);

          return (
            <button
              key={scenario.id}
              onClick={() => handleScenarioChange(scenario.id)}
              className={`p-2 rounded-lg transition-all duration-200 ${
                isActive
                  ? themeClasses
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={scenario.name}
            >
              <Icon className="h-4 w-4" />
            </button>
          );
        })}
      </div>
    );
  }

  // 默认下拉变体
  return (
    <div className={`relative ${className}`}>
      {showLabel && (
        <label className="block text-sm font-medium text-gray-300 mb-2">
          当前场景
        </label>
      )}

      <div className="relative">
        <Button
          variant="outline"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full justify-between bg-white border-gray-300 hover:bg-gray-50"
        >
          <div className="flex items-center space-x-2">
            {state.currentScenario && (
              <>
                {React.createElement(getScenarioIcon(state.currentScenario.id), {
                  className: `h-4 w-4 ${getThemeClasses(state.currentScenario.id).split(' ')[0]}`
                })}
                <span className="text-gray-900">
                  {state.currentScenario.name}
                </span>
              </>
            )}
          </div>
          <ChevronDown className={`h-4 w-4 text-gray-500 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`} />
        </Button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
            <div className="py-1">
              {state.availableScenarios.map((scenario) => {
                const Icon = getScenarioIcon(scenario.id);
                const isActive = state.currentScenario?.id === scenario.id;
                const themeClasses = getThemeClasses(scenario.id);

                return (
                  <button
                    key={scenario.id}
                    onClick={() => handleScenarioChange(scenario.id)}
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center space-x-3 transition-colors ${
                      isActive ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className={`p-1.5 rounded ${
                      isActive ? themeClasses : 'bg-gray-100 text-gray-600'
                    }`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">
                          {scenario.name}
                        </span>
                        {isActive && (
                          <Check className="h-4 w-4 text-green-600" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 truncate">
                        {scenario.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 点击外部关闭下拉框 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
