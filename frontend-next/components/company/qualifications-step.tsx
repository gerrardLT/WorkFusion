'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Plus, Trash2 } from 'lucide-react';
import type { Company, Qualification } from '@/types/company';

interface QualificationsStepProps {
  formData: Partial<Company>;
  updateFormData: (data: Partial<Company>) => void;
}

export default function QualificationsStep({ formData, updateFormData }: QualificationsStepProps) {
  const qualifications = formData.qualifications || [];

  const addQualification = () => {
    const newQualification: Qualification = {
      name: '',
      level: '',
      number: '',
      expire_date: '',
    };
    updateFormData({
      qualifications: [...qualifications, newQualification],
    });
  };

  const updateQualification = (index: number, field: keyof Qualification, value: string) => {
    const updated = [...qualifications];
    updated[index] = { ...updated[index], [field]: value };
    updateFormData({ qualifications: updated });
  };

  const removeQualification = (index: number) => {
    const updated = qualifications.filter((_, i) => i !== index);
    updateFormData({ qualifications: updated });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">资质管理</h2>
        <p className="text-gray-400 text-sm mb-6">
          添加企业持有的资质证书、许可证等，帮助系统更准确地匹配项目
        </p>
      </div>

      {/* 资质列表 */}
      <div className="space-y-4">
        {qualifications.map((qualification, index) => (
          <Card key={index} className="bg-gray-700 border-gray-600 p-4">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-md font-semibold text-white">资质 #{index + 1}</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeQualification(index)}
                className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 资质名称 */}
              <div className="md:col-span-2">
                <Label htmlFor={`qual-name-${index}`} className="text-gray-300">
                  资质名称 <span className="text-red-500">*</span>
                </Label>
                <Input
                  id={`qual-name-${index}`}
                  value={qualification.name}
                  onChange={(e) => updateQualification(index, 'name', e.target.value)}
                  placeholder="如：建筑工程施工总承包一级资质"
                  className="bg-gray-800 border-gray-600 text-white mt-2"
                  required
                />
              </div>

              {/* 资质等级 */}
              <div>
                <Label htmlFor={`qual-level-${index}`} className="text-gray-300">
                  资质等级
                </Label>
                <Input
                  id={`qual-level-${index}`}
                  value={qualification.level}
                  onChange={(e) => updateQualification(index, 'level', e.target.value)}
                  placeholder="如：一级、甲级、AAA级"
                  className="bg-gray-800 border-gray-600 text-white mt-2"
                />
              </div>

              {/* 证书编号 */}
              <div>
                <Label htmlFor={`qual-number-${index}`} className="text-gray-300">
                  证书编号
                </Label>
                <Input
                  id={`qual-number-${index}`}
                  value={qualification.number || ''}
                  onChange={(e) => updateQualification(index, 'number', e.target.value)}
                  placeholder="证书编号"
                  className="bg-gray-800 border-gray-600 text-white mt-2"
                />
              </div>

              {/* 有效期至 */}
              <div>
                <Label htmlFor={`qual-expire-${index}`} className="text-gray-300">
                  有效期至
                </Label>
                <Input
                  id={`qual-expire-${index}`}
                  type="date"
                  value={qualification.expire_date || ''}
                  onChange={(e) => updateQualification(index, 'expire_date', e.target.value)}
                  className="bg-gray-800 border-gray-600 text-white mt-2"
                />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 添加资质按钮 */}
      <Button
        variant="outline"
        onClick={addQualification}
        className="w-full border-gray-600 text-gray-300 hover:bg-gray-700"
      >
        <Plus className="h-4 w-4 mr-2" />
        添加资质
      </Button>

      {/* 常见资质示例 */}
      <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-300 mb-2">💡 常见资质示例</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• 建筑业企业资质（一级/二级/三级）</li>
          <li>• 工程设计资质（甲级/乙级/丙级）</li>
          <li>• 工程勘察资质（综合/专业）</li>
          <li>• ISO 9001质量管理体系认证</li>
          <li>• ISO 14001环境管理体系认证</li>
          <li>• ISO 45001职业健康安全管理体系认证</li>
          <li>• 安全生产许可证</li>
          <li>• 特种设备制造许可证</li>
        </ul>
      </div>
    </div>
  );
}

