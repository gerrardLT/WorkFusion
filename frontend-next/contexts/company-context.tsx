'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Company } from '@/types/company';

interface CompanyState {
  currentCompany: Company | null;
  isLoading: boolean;
}

interface CompanyContextValue {
  state: CompanyState;
  setCurrentCompany: (company: Company | null) => void;
  clearCurrentCompany: () => void;
}

const CompanyContext = createContext<CompanyContextValue | null>(null);

interface CompanyProviderProps {
  children: ReactNode;
}

export function CompanyProvider({ children }: CompanyProviderProps) {
  const [state, setState] = useState<CompanyState>({
    currentCompany: null,
    isLoading: true,
  });

  // 从 localStorage 加载公司信息
  useEffect(() => {
    const loadCompany = () => {
      try {
        const stored = localStorage.getItem('current_company');
        if (stored) {
          const company = JSON.parse(stored) as Company;
          setState({ currentCompany: company, isLoading: false });
        } else {
          setState({ currentCompany: null, isLoading: false });
        }
      } catch (error) {
        console.error('加载公司信息失败:', error);
        setState({ currentCompany: null, isLoading: false });
      }
    };

    loadCompany();
  }, []);

  // 设置当前公司
  const setCurrentCompany = (company: Company | null) => {
    setState({ currentCompany: company, isLoading: false });

    if (company) {
      localStorage.setItem('current_company', JSON.stringify(company));
    } else {
      localStorage.removeItem('current_company');
    }
  };

  // 清除当前公司
  const clearCurrentCompany = () => {
    setState({ currentCompany: null, isLoading: false });
    localStorage.removeItem('current_company');
  };

  const contextValue: CompanyContextValue = {
    state,
    setCurrentCompany,
    clearCurrentCompany,
  };

  return (
    <CompanyContext.Provider value={contextValue}>
      {children}
    </CompanyContext.Provider>
  );
}

// Hook
export function useCompany() {
  const context = useContext(CompanyContext);
  if (!context) {
    throw new Error('useCompany必须在CompanyProvider内使用');
  }
  return context;
}

