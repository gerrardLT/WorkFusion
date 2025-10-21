'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ArrowRight, Save, Check } from 'lucide-react';
import { useScenario } from '@/contexts/scenario-context';
import { useCompany } from '@/contexts/company-context';
import BasicInfoStep from '@/components/company/basic-info-step';
import QualificationsStep from '@/components/company/qualifications-step';
import CapabilitiesStep from '@/components/company/capabilities-step';
import TargetMarketStep from '@/components/company/target-market-step';
import { createCompany } from '@/lib/api-v2';
import type { Company } from '@/types/company';

const STEPS = [
  { id: 1, name: '基本信息', description: '企业基础资料' },
  { id: 2, name: '资质管理', description: '证书与资质' },
  { id: 3, name: '能力描述', description: '专业领域与优势' },
  { id: 4, name: '目标市场', description: '区域与预算范围' },
];

export default function CompanyProfilePage() {
  const router = useRouter();
  const { state } = useScenario();
  const { setCurrentCompany } = useCompany();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 表单数据
  const [formData, setFormData] = useState<Partial<Company>>({
    name: '',
    description: '',
    scale: 'medium',
    employee_count: undefined,
    registered_capital: undefined,
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: '',
    website: '',
    qualifications: [],
    capabilities: {
      fields: [],
      advantages: [],
      certifications: [],
      patents: 0,
      projects_completed: 0,
    },
    achievements: {
      total_projects: 0,
      total_amount: 0,
      average_amount: 0,
      success_rate: 0,
      major_projects: [],
      clients: [],
    },
    target_areas: [],
    target_industries: [],
    budget_range: { min: 0, max: 0 },
    preferences: {},
  });

  // 更新表单数据
  const updateFormData = (data: Partial<Company>) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  // 保存草稿
  const handleSaveDraft = async () => {
    setIsSaving(true);
    try {
      // 保存到localStorage
      localStorage.setItem('company_draft', JSON.stringify({
        formData,
        currentStep,
        timestamp: new Date().toISOString(),
      }));
      alert('草稿已保存');
    } catch (error) {
      console.error('保存草稿失败:', error);
      alert('保存草稿失败');
    } finally {
      setIsSaving(false);
    }
  };

  // 加载草稿
  const loadDraft = () => {
    try {
      const draft = localStorage.getItem('company_draft');
      if (draft) {
        const parsed = JSON.parse(draft);
        if (confirm(`发现草稿（${new Date(parsed.timestamp).toLocaleString()}），是否恢复？`)) {
          setFormData(parsed.formData);
          setCurrentStep(parsed.currentStep);
        }
      }
    } catch (error) {
      console.error('加载草稿失败:', error);
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const company = await createCompany({
        ...formData,
        scenario_id: state.currentScenario?.id || 'tender',
      } as any);

      // 保存到CompanyContext
      setCurrentCompany(company);

      // 清除草稿
      localStorage.removeItem('company_draft');

      alert('企业画像创建成功！');
      router.push('/projects'); // 跳转到项目推荐页面
    } catch (error: any) {
      console.error('提交失败:', error);
      alert(error.message || '提交失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 下一步
  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  // 上一步
  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // 页面加载时检查草稿
  useState(() => {
    loadDraft();
  });

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* 标题 */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            className="mb-4 text-gray-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回首页
          </Button>
          <h1 className="text-3xl font-bold text-white mb-2">企业画像设置</h1>
          <p className="text-gray-400">完善企业信息，获得更精准的项目推荐</p>
        </div>

        {/* 步骤指示器 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center">
                  <div
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center font-semibold
                      ${currentStep === step.id
                        ? 'bg-blue-600 text-white'
                        : currentStep > step.id
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-700 text-gray-400'
                      }
                    `}
                  >
                    {currentStep > step.id ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      step.id
                    )}
                  </div>
                  <div className="mt-2 text-center">
                    <div className={`text-sm font-medium ${currentStep >= step.id ? 'text-white' : 'text-gray-500'}`}>
                      {step.name}
                    </div>
                    <div className="text-xs text-gray-500">{step.description}</div>
                  </div>
                </div>
                {index < STEPS.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-4 ${currentStep > step.id ? 'bg-green-600' : 'bg-gray-700'}`} />
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* 表单内容 */}
        <Card className="bg-gray-800 border-gray-700 p-8 mb-6">
          {currentStep === 1 && (
            <BasicInfoStep formData={formData} updateFormData={updateFormData} />
          )}
          {currentStep === 2 && (
            <QualificationsStep formData={formData} updateFormData={updateFormData} />
          )}
          {currentStep === 3 && (
            <CapabilitiesStep formData={formData} updateFormData={updateFormData} />
          )}
          {currentStep === 4 && (
            <TargetMarketStep formData={formData} updateFormData={updateFormData} />
          )}
        </Card>

        {/* 操作按钮 */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            上一步
          </Button>

          <Button
            variant="outline"
            onClick={handleSaveDraft}
            disabled={isSaving}
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? '保存中...' : '保存草稿'}
          </Button>

          <Button
            onClick={handleNext}
            disabled={isSubmitting}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {currentStep === STEPS.length ? (
              <>
                {isSubmitting ? '提交中...' : '完成'}
                <Check className="h-4 w-4 ml-2" />
              </>
            ) : (
              <>
                下一步
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

