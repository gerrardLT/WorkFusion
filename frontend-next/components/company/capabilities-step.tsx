'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Plus, X } from 'lucide-react';
import type { Company, Capabilities } from '@/types/company';

interface CapabilitiesStepProps {
  formData: Partial<Company>;
  updateFormData: (data: Partial<Company>) => void;
}

// 预设的专业领域
const PRESET_FIELDS = [
  '电力工程', '输变电工程', '配电工程', '新能源发电',
  '智能电网', '电力自动化', '电力通信', '电力设计',
  '工程监理', '设备安装', '运维服务', '技术咨询',
];

// 预设的核心优势
const PRESET_ADVANTAGES = [
  '技术创新能力强', '项目经验丰富', '施工质量优秀',
  '工期保障能力强', '成本控制优秀', '安全管理规范',
  '团队专业素质高', '售后服务完善', '设备先进',
];

export default function CapabilitiesStep({ formData, updateFormData }: CapabilitiesStepProps) {
  const capabilities = formData.capabilities || {
    fields: [],
    advantages: [],
    certifications: [],
    patents: 0,
    projects_completed: 0,
  };

  const [customField, setCustomField] = useState('');
  const [customAdvantage, setCustomAdvantage] = useState('');
  const [customCertification, setCustomCertification] = useState('');

  // 切换专业领域
  const toggleField = (field: string) => {
    const fields = capabilities.fields || [];
    const updated = fields.includes(field)
      ? fields.filter((f) => f !== field)
      : [...fields, field];
    updateFormData({ capabilities: { ...capabilities, fields: updated } });
  };

  // 添加自定义专业领域
  const addCustomField = () => {
    if (customField.trim() && !capabilities.fields.includes(customField.trim())) {
      updateFormData({
        capabilities: {
          ...capabilities,
          fields: [...capabilities.fields, customField.trim()],
        },
      });
      setCustomField('');
    }
  };

  // 切换核心优势
  const toggleAdvantage = (advantage: string) => {
    const advantages = capabilities.advantages || [];
    const updated = advantages.includes(advantage)
      ? advantages.filter((a) => a !== advantage)
      : [...advantages, advantage];
    updateFormData({ capabilities: { ...capabilities, advantages: updated } });
  };

  // 添加自定义优势
  const addCustomAdvantage = () => {
    if (customAdvantage.trim() && !capabilities.advantages.includes(customAdvantage.trim())) {
      updateFormData({
        capabilities: {
          ...capabilities,
          advantages: [...capabilities.advantages, customAdvantage.trim()],
        },
      });
      setCustomAdvantage('');
    }
  };

  // 添加认证证书
  const addCertification = () => {
    if (customCertification.trim() && !capabilities.certifications.includes(customCertification.trim())) {
      updateFormData({
        capabilities: {
          ...capabilities,
          certifications: [...capabilities.certifications, customCertification.trim()],
        },
      });
      setCustomCertification('');
    }
  };

  // 移除认证证书
  const removeCertification = (cert: string) => {
    updateFormData({
      capabilities: {
        ...capabilities,
        certifications: capabilities.certifications.filter((c) => c !== cert),
      },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">能力描述</h2>
        <p className="text-gray-400 text-sm mb-6">
          展示企业的专业领域、核心优势和技术能力
        </p>
      </div>

      {/* 专业领域 */}
      <div>
        <Label className="text-gray-300 mb-3 block">
          专业领域 <span className="text-red-500">*</span>
          <span className="text-xs text-gray-500 ml-2">（至少选择一项）</span>
        </Label>
        <div className="flex flex-wrap gap-2 mb-3">
          {PRESET_FIELDS.map((field) => (
            <Badge
              key={field}
              variant={capabilities.fields.includes(field) ? 'default' : 'outline'}
              className={`cursor-pointer ${
                capabilities.fields.includes(field)
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => toggleField(field)}
            >
              {field}
              {capabilities.fields.includes(field) && <X className="ml-1 h-3 w-3" />}
            </Badge>
          ))}
        </div>
        {/* 自定义领域 */}
        <div className="flex gap-2">
          <Input
            value={customField}
            onChange={(e) => setCustomField(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCustomField()}
            placeholder="输入其他专业领域"
            className="bg-gray-700 border-gray-600 text-white flex-1"
          />
          <Button
            type="button"
            onClick={addCustomField}
            variant="outline"
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 核心优势 */}
      <div>
        <Label className="text-gray-300 mb-3 block">
          核心优势
          <span className="text-xs text-gray-500 ml-2">（可多选）</span>
        </Label>
        <div className="flex flex-wrap gap-2 mb-3">
          {PRESET_ADVANTAGES.map((advantage) => (
            <Badge
              key={advantage}
              variant={capabilities.advantages.includes(advantage) ? 'default' : 'outline'}
              className={`cursor-pointer ${
                capabilities.advantages.includes(advantage)
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => toggleAdvantage(advantage)}
            >
              {advantage}
              {capabilities.advantages.includes(advantage) && <X className="ml-1 h-3 w-3" />}
            </Badge>
          ))}
        </div>
        {/* 自定义优势 */}
        <div className="flex gap-2">
          <Input
            value={customAdvantage}
            onChange={(e) => setCustomAdvantage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCustomAdvantage()}
            placeholder="输入其他核心优势"
            className="bg-gray-700 border-gray-600 text-white flex-1"
          />
          <Button
            type="button"
            onClick={addCustomAdvantage}
            variant="outline"
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 认证证书 */}
      <div>
        <Label className="text-gray-300 mb-3 block">
          体系认证证书
          <span className="text-xs text-gray-500 ml-2">（如ISO系列认证）</span>
        </Label>

        {/* 已添加的证书 */}
        {capabilities.certifications.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {capabilities.certifications.map((cert, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="bg-gray-700 text-gray-300 border-gray-600"
              >
                {cert}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer hover:text-red-400"
                  onClick={() => removeCertification(cert)}
                />
              </Badge>
            ))}
          </div>
        )}

        {/* 添加证书 */}
        <div className="flex gap-2">
          <Input
            value={customCertification}
            onChange={(e) => setCustomCertification(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCertification()}
            placeholder="如：ISO 9001:2015 质量管理体系认证"
            className="bg-gray-700 border-gray-600 text-white flex-1"
          />
          <Button
            type="button"
            onClick={addCertification}
            variant="outline"
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 统计数据 */}
      <Card className="bg-gray-700 border-gray-600 p-6">
        <h3 className="text-md font-semibold text-white mb-4">技术实力数据</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 专利数量 */}
          <div>
            <Label htmlFor="patents" className="text-gray-300">
              拥有专利数量
            </Label>
            <Input
              id="patents"
              type="number"
              value={capabilities.patents || ''}
              onChange={(e) =>
                updateFormData({
                  capabilities: {
                    ...capabilities,
                    patents: parseInt(e.target.value) || 0,
                  },
                })
              }
              placeholder="专利总数"
              min="0"
              className="bg-gray-800 border-gray-600 text-white mt-2"
            />
          </div>

          {/* 完成项目数 */}
          <div>
            <Label htmlFor="projects_completed" className="text-gray-300">
              累计完成项目数
            </Label>
            <Input
              id="projects_completed"
              type="number"
              value={capabilities.projects_completed || ''}
              onChange={(e) =>
                updateFormData({
                  capabilities: {
                    ...capabilities,
                    projects_completed: parseInt(e.target.value) || 0,
                  },
                })
              }
              placeholder="项目总数"
              min="0"
              className="bg-gray-800 border-gray-600 text-white mt-2"
            />
          </div>
        </div>
      </Card>
    </div>
  );
}

