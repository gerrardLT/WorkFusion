'use client';

import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useScenario } from '@/contexts/scenario-context';

interface ThemeContextValue {
  applyScenarioTheme: (scenarioId: string) => void;
  getCurrentThemeClasses: () => {
    primary: string;
    secondary: string;
    gradient: string;
    text: string;
    background: string;
    border: string;
    hover: string;
  };
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

interface DynamicThemeProviderProps {
  children: ReactNode;
}

export function DynamicThemeProvider({ children }: DynamicThemeProviderProps) {
  const { state, getCurrentTheme } = useScenario();

  // 应用场景主题
  const applyScenarioTheme = (scenarioId: string) => {
    const scenario = state.availableScenarios.find(s => s.id === scenarioId);
    if (!scenario || !scenario.theme) return;

    const theme = scenario.theme;
    const root = document.documentElement;

    // 根据主题颜色设置CSS变量
    switch (theme.primaryColor) {
      case 'blue':
        root.style.setProperty('--theme-primary', '59 130 246'); // blue-500
        root.style.setProperty('--theme-primary-dark', '37 99 235'); // blue-600
        root.style.setProperty('--theme-primary-light', '147 197 253'); // blue-300
        root.style.setProperty('--theme-gradient-from', '37 99 235'); // blue-600
        root.style.setProperty('--theme-gradient-to', '147 51 234'); // purple-600
        break;
      case 'green':
        root.style.setProperty('--theme-primary', '34 197 94'); // green-500
        root.style.setProperty('--theme-primary-dark', '22 163 74'); // green-600
        root.style.setProperty('--theme-primary-light', '134 239 172'); // green-300
        root.style.setProperty('--theme-gradient-from', '22 163 74'); // green-600
        root.style.setProperty('--theme-gradient-to', '20 184 166'); // teal-600
        break;
      case 'purple':
        root.style.setProperty('--theme-primary', '168 85 247'); // purple-500
        root.style.setProperty('--theme-primary-dark', '147 51 234'); // purple-600
        root.style.setProperty('--theme-primary-light', '196 181 253'); // purple-300
        root.style.setProperty('--theme-gradient-from', '147 51 234'); // purple-600
        root.style.setProperty('--theme-gradient-to', '219 39 119'); // pink-600
        break;
      case 'orange':
        // 将橙色主题改为红色主题
        root.style.setProperty('--theme-primary', '239 68 68'); // red-500
        root.style.setProperty('--theme-primary-dark', '220 38 38'); // red-600
        root.style.setProperty('--theme-primary-light', '252 165 165'); // red-300
        root.style.setProperty('--theme-gradient-from', '220 38 38'); // red-600
        root.style.setProperty('--theme-gradient-to', '219 39 119'); // pink-600
        break;
      default:
        // 默认蓝色主题
        root.style.setProperty('--theme-primary', '59 130 246');
        root.style.setProperty('--theme-primary-dark', '37 99 235');
        root.style.setProperty('--theme-primary-light', '147 197 253');
        root.style.setProperty('--theme-gradient-from', '37 99 235');
        root.style.setProperty('--theme-gradient-to', '147 51 234');
    }
  };

  // 获取当前主题的Tailwind类名
  const getCurrentThemeClasses = () => {
    const theme = getCurrentTheme();
    if (!theme) {
      return {
        primary: 'text-blue-600',
        secondary: 'text-blue-500',
        gradient: 'from-blue-600 to-purple-600',
        text: 'text-blue-700',
        background: 'bg-blue-50',
        border: 'border-blue-200',
        hover: 'hover:bg-blue-100',
      };
    }

    switch (theme.primaryColor) {
      case 'blue':
        return {
          primary: 'text-blue-600',
          secondary: 'text-blue-500',
          gradient: 'from-blue-600 to-purple-600',
          text: 'text-blue-700',
          background: 'bg-blue-50',
          border: 'border-blue-200',
          hover: 'hover:bg-blue-100',
        };
      case 'green':
        return {
          primary: 'text-green-600',
          secondary: 'text-green-500',
          gradient: 'from-green-600 to-teal-600',
          text: 'text-green-700',
          background: 'bg-green-50',
          border: 'border-green-200',
          hover: 'hover:bg-green-100',
        };
      case 'purple':
        return {
          primary: 'text-purple-600',
          secondary: 'text-purple-500',
          gradient: 'from-purple-600 to-pink-600',
          text: 'text-purple-700',
          background: 'bg-purple-50',
          border: 'border-purple-200',
          hover: 'hover:bg-purple-100',
        };
      case 'orange':
        // 将橙色主题改为红色主题
        return {
          primary: 'text-red-600',
          secondary: 'text-red-500',
          gradient: 'from-red-600 to-pink-600',
          text: 'text-red-700',
          background: 'bg-red-50',
          border: 'border-red-200',
          hover: 'hover:bg-red-100',
        };
      default:
        return {
          primary: 'text-blue-600',
          secondary: 'text-blue-500',
          gradient: 'from-blue-600 to-purple-600',
          text: 'text-blue-700',
          background: 'bg-blue-50',
          border: 'border-blue-200',
          hover: 'hover:bg-blue-100',
        };
    }
  };

  // 监听场景变化并应用主题
  useEffect(() => {
    if (state.currentScenario) {
      applyScenarioTheme(state.currentScenario.id);
    }
  }, [state.currentScenario]);

  const contextValue: ThemeContextValue = {
    applyScenarioTheme,
    getCurrentThemeClasses,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

// Hook for using theme context
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a DynamicThemeProvider');
  }
  return context;
}

// Higher-order component for themed components
export function withTheme<P extends object>(
  Component: React.ComponentType<P & { themeClasses: ReturnType<ThemeContextValue['getCurrentThemeClasses']> }>
) {
  return function ThemedComponent(props: P) {
    const { getCurrentThemeClasses } = useTheme();
    const themeClasses = getCurrentThemeClasses();

    return <Component {...props} themeClasses={themeClasses} />;
  };
}

// Utility function to generate theme-aware CSS classes
export function getThemeClass(
  baseClass: string,
  themeType: 'primary' | 'secondary' | 'gradient' | 'text' | 'background' | 'border' | 'hover',
  currentScenario?: { theme: { primaryColor: string } }
): string {
  if (!currentScenario) return baseClass;

  const color = currentScenario.theme.primaryColor;

  const colorMap = {
    blue: {
      primary: 'blue-600',
      secondary: 'blue-500',
      gradient: 'from-blue-600 to-purple-600',
      text: 'blue-700',
      background: 'blue-50',
      border: 'blue-200',
      hover: 'hover:bg-blue-100',
    },
    green: {
      primary: 'green-600',
      secondary: 'green-500',
      gradient: 'from-green-600 to-teal-600',
      text: 'green-700',
      background: 'green-50',
      border: 'green-200',
      hover: 'hover:bg-green-100',
    },
    purple: {
      primary: 'purple-600',
      secondary: 'purple-500',
      gradient: 'from-purple-600 to-pink-600',
      text: 'purple-700',
      background: 'purple-50',
      border: 'purple-200',
      hover: 'hover:bg-purple-100',
    },
    orange: {
      // 将橙色改为红色
      primary: 'red-600',
      secondary: 'red-500',
      gradient: 'from-red-600 to-pink-600',
      text: 'red-700',
      background: 'red-50',
      border: 'red-200',
      hover: 'hover:bg-red-100',
    },
  };

  const themeColors = colorMap[color as keyof typeof colorMap] || colorMap.blue;
  const themeValue = themeColors[themeType];

  if (themeType === 'gradient') {
    return `bg-gradient-to-r ${themeValue}`;
  }

  if (themeType === 'hover') {
    return themeValue;
  }

  // 替换基础类中的颜色部分
  const colorRegex = /(text-|bg-|border-)(blue|green|purple|red|gray)(-\d+)?/g;
  const prefix = themeType === 'text' ? 'text-' : themeType === 'background' ? 'bg-' : 'border-';

  if (baseClass.includes(prefix)) {
    return baseClass.replace(colorRegex, `${prefix}${themeValue}`);
  }

  return `${baseClass} ${prefix}${themeValue}`;
}
