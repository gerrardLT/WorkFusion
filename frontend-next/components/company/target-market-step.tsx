'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Plus, X } from 'lucide-react';
import type { Company } from '@/types/company';

interface TargetMarketStepProps {
  formData: Partial<Company>;
  updateFormData: (data: Partial<Company>) => void;
}

// 预设的省份/地区
const PRESET_AREAS = [
  '北京', '上海', '天津', '重庆',
  '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '江苏', '浙江', '安徽', '福建', '江西', '山东',
  '河南', '湖北', '湖南', '广东', '广西', '海南',
  '四川', '贵州', '云南', '西藏', '陕西', '甘肃',
  '青海', '宁夏', '新疆',
];

// 预设的行业领域
const PRESET_INDUSTRIES = [
  '电力能源', '石油化工', '交通运输', '水利水务',
  '建筑工程', '市政公用', '环境保护', '信息通信',
  '制造业', '教育医疗', '政府机关', '金融保险',
];

export default function TargetMarketStep({ formData, updateFormData }: TargetMarketStepProps) {
  const targetAreas = formData.target_areas || [];
  const targetIndustries = formData.target_industries || [];
  const budgetRange = formData.budget_range || { min: 0, max: 0 };

  const [customArea, setCustomArea] = useState('');
  const [customIndustry, setCustomIndustry] = useState('');

  // 切换目标区域
  const toggleArea = (area: string) => {
    const updated = targetAreas.includes(area)
      ? targetAreas.filter((a) => a !== area)
      : [...targetAreas, area];
    updateFormData({ target_areas: updated });
  };

  // 添加自定义区域
  const addCustomArea = () => {
    if (customArea.trim() && !targetAreas.includes(customArea.trim())) {
      updateFormData({ target_areas: [...targetAreas, customArea.trim()] });
      setCustomArea('');
    }
  };

  // 切换目标行业
  const toggleIndustry = (industry: string) => {
    const updated = targetIndustries.includes(industry)
      ? targetIndustries.filter((i) => i !== industry)
      : [...targetIndustries, industry];
    updateFormData({ target_industries: updated });
  };

  // 添加自定义行业
  const addCustomIndustry = () => {
    if (customIndustry.trim() && !targetIndustries.includes(customIndustry.trim())) {
      updateFormData({ target_industries: [...targetIndustries, customIndustry.trim()] });
      setCustomIndustry('');
    }
  };

  // 快捷选择（全国）
  const selectAllAreas = () => {
    updateFormData({ target_areas: ['全国'] });
  };

  // 快捷选择（华东/华南/华北等）
  const selectRegion = (region: string) => {
    const regions: Record<string, string[]> = {
      华东: ['上海', '江苏', '浙江', '安徽', '福建', '江西', '山东'],
      华南: ['广东', '广西', '海南'],
      华北: ['北京', '天津', '河北', '山西', '内蒙古'],
      华中: ['河南', '湖北', '湖南'],
      西南: ['重庆', '四川', '贵州', '云南', '西藏'],
      西北: ['陕西', '甘肃', '青海', '宁夏', '新疆'],
      东北: ['辽宁', '吉林', '黑龙江'],
    };
    const areas = regions[region] || [];
    const combined = Array.from(new Set([...targetAreas, ...areas]));
    updateFormData({ target_areas: combined });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">目标市场</h2>
        <p className="text-gray-400 text-sm mb-6">
          设定您希望参与项目的地区、行业和预算范围，系统将为您推荐匹配的项目
        </p>
      </div>

      {/* 目标区域 */}
      <div>
        <Label className="text-gray-300 mb-3 block">
          目标区域 <span className="text-red-500">*</span>
          <span className="text-xs text-gray-500 ml-2">（至少选择一项）</span>
        </Label>

        {/* 快捷选择 */}
        <div className="flex flex-wrap gap-2 mb-3">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={selectAllAreas}
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            全国
          </Button>
          {['华东', '华南', '华北', '华中', '西南', '西北', '东北'].map((region) => (
            <Button
              key={region}
              type="button"
              size="sm"
              variant="outline"
              onClick={() => selectRegion(region)}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              {region}
            </Button>
          ))}
        </div>

        {/* 省份选择 */}
        <div className="flex flex-wrap gap-2 mb-3">
          {PRESET_AREAS.map((area) => (
            <Badge
              key={area}
              variant={targetAreas.includes(area) ? 'default' : 'outline'}
              className={`cursor-pointer ${
                targetAreas.includes(area)
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => toggleArea(area)}
            >
              {area}
              {targetAreas.includes(area) && <X className="ml-1 h-3 w-3" />}
            </Badge>
          ))}
        </div>

        {/* 自定义区域 */}
        <div className="flex gap-2">
          <Input
            value={customArea}
            onChange={(e) => setCustomArea(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCustomArea()}
            placeholder="输入其他目标区域"
            className="bg-gray-700 border-gray-600 text-white flex-1"
          />
          <Button
            type="button"
            onClick={addCustomArea}
            variant="outline"
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 目标行业 */}
      <div>
        <Label className="text-gray-300 mb-3 block">
          目标行业 <span className="text-red-500">*</span>
          <span className="text-xs text-gray-500 ml-2">（至少选择一项）</span>
        </Label>
        <div className="flex flex-wrap gap-2 mb-3">
          {PRESET_INDUSTRIES.map((industry) => (
            <Badge
              key={industry}
              variant={targetIndustries.includes(industry) ? 'default' : 'outline'}
              className={`cursor-pointer ${
                targetIndustries.includes(industry)
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => toggleIndustry(industry)}
            >
              {industry}
              {targetIndustries.includes(industry) && <X className="ml-1 h-3 w-3" />}
            </Badge>
          ))}
        </div>

        {/* 自定义行业 */}
        <div className="flex gap-2">
          <Input
            value={customIndustry}
            onChange={(e) => setCustomIndustry(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCustomIndustry()}
            placeholder="输入其他目标行业"
            className="bg-gray-700 border-gray-600 text-white flex-1"
          />
          <Button
            type="button"
            onClick={addCustomIndustry}
            variant="outline"
            className="border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 预算范围 */}
      <Card className="bg-gray-700 border-gray-600 p-6">
        <h3 className="text-md font-semibold text-white mb-4">项目预算范围（万元）</h3>
        <p className="text-xs text-gray-400 mb-4">
          设定您希望参与的项目预算区间，留空表示不限制
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 最小预算 */}
          <div>
            <Label htmlFor="budget_min" className="text-gray-300">
              最小预算（万元）
            </Label>
            <Input
              id="budget_min"
              type="number"
              value={budgetRange.min || ''}
              onChange={(e) =>
                updateFormData({
                  budget_range: {
                    ...budgetRange,
                    min: parseInt(e.target.value) || 0,
                  },
                })
              }
              placeholder="如：100"
              min="0"
              className="bg-gray-800 border-gray-600 text-white mt-2"
            />
          </div>

          {/* 最大预算 */}
          <div>
            <Label htmlFor="budget_max" className="text-gray-300">
              最大预算（万元）
            </Label>
            <Input
              id="budget_max"
              type="number"
              value={budgetRange.max || ''}
              onChange={(e) =>
                updateFormData({
                  budget_range: {
                    ...budgetRange,
                    max: parseInt(e.target.value) || 0,
                  },
                })
              }
              placeholder="如：1000"
              min="0"
              className="bg-gray-800 border-gray-600 text-white mt-2"
            />
          </div>
        </div>

        {/* 预算提示 */}
        <div className="mt-4 bg-gray-800/50 border border-gray-600 rounded p-3">
          <p className="text-xs text-gray-400">
            💡 提示：系统将优先推荐符合您预算范围的项目，但也会推荐一些略超预算的优质项目供参考
          </p>
        </div>
      </Card>

      {/* 总结 */}
      <Card className="bg-blue-900/20 border-blue-800 p-4">
        <h4 className="text-sm font-semibold text-blue-300 mb-2">🎯 目标市场总结</h4>
        <div className="space-y-2 text-xs text-gray-300">
          <div>
            <span className="font-medium">目标区域：</span>
            {targetAreas.length > 0 ? targetAreas.join('、') : '未设置'}
          </div>
          <div>
            <span className="font-medium">目标行业：</span>
            {targetIndustries.length > 0 ? targetIndustries.join('、') : '未设置'}
          </div>
          <div>
            <span className="font-medium">预算范围：</span>
            {budgetRange.min > 0 || budgetRange.max > 0
              ? `${budgetRange.min || 0} - ${budgetRange.max || '不限'} 万元`
              : '不限'}
          </div>
        </div>
      </Card>
    </div>
  );
}

