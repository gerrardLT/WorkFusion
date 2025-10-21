'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Filter, X, ArrowUpDown } from 'lucide-react';
import type { ProjectFilters as Filters, ProjectSortOptions } from '@/types/project';

interface ProjectFiltersProps {
  filters: Filters;
  sortOptions: ProjectSortOptions;
  onApplyFilters: (filters: Filters) => void;
  onApplySort: (sort: ProjectSortOptions) => void;
}

// 预设地区
const PRESET_AREAS = [
  '北京', '上海', '天津', '重庆',
  '江苏', '浙江', '广东', '福建',
  '山东', '河北', '河南', '湖北',
  '湖南', '四川', '陕西', '辽宁',
];

// 预设行业
const PRESET_INDUSTRIES = [
  '电力能源', '石油化工', '交通运输', '水利水务',
  '建筑工程', '市政公用', '环境保护', '信息通信',
];

export default function ProjectFilters({
  filters,
  sortOptions,
  onApplyFilters,
  onApplySort,
}: ProjectFiltersProps) {
  const [localFilters, setLocalFilters] = useState<Filters>(filters);
  const [localSort, setLocalSort] = useState<ProjectSortOptions>(sortOptions);
  const [selectedAreas, setSelectedAreas] = useState<string[]>(filters.areas || []);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>(filters.industries || []);

  // 切换地区
  const toggleArea = (area: string) => {
    const updated = selectedAreas.includes(area)
      ? selectedAreas.filter((a) => a !== area)
      : [...selectedAreas, area];
    setSelectedAreas(updated);
    setLocalFilters({ ...localFilters, areas: updated });
  };

  // 切换行业
  const toggleIndustry = (industry: string) => {
    const updated = selectedIndustries.includes(industry)
      ? selectedIndustries.filter((i) => i !== industry)
      : [...selectedIndustries, industry];
    setSelectedIndustries(updated);
    setLocalFilters({ ...localFilters, industries: updated });
  };

  // 应用筛选
  const handleApply = () => {
    onApplyFilters(localFilters);
    onApplySort(localSort);
  };

  // 重置筛选
  const handleReset = () => {
    const resetFilters: Filters = { min_score: 70 };
    const resetSort: ProjectSortOptions = { sort_by: 'match_score', order: 'desc' };
    setLocalFilters(resetFilters);
    setLocalSort(resetSort);
    setSelectedAreas([]);
    setSelectedIndustries([]);
    onApplyFilters(resetFilters);
    onApplySort(resetSort);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-white">筛选与排序</h3>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="text-gray-400 hover:text-white"
          >
            重置
          </Button>
          <Button
            size="sm"
            onClick={handleApply}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            应用筛选
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* 匹配度 */}
        <div>
          <Label htmlFor="min_score" className="text-gray-300 mb-2 block">
            最低匹配度
          </Label>
          <Select
            value={localFilters.min_score?.toString() || '70'}
            onValueChange={(value) =>
              setLocalFilters({ ...localFilters, min_score: parseInt(value) })
            }
          >
            <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
              <SelectValue placeholder="选择匹配度" />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="90" className="text-gray-300">90分以上</SelectItem>
              <SelectItem value="80" className="text-gray-300">80分以上</SelectItem>
              <SelectItem value="70" className="text-gray-300">70分以上</SelectItem>
              <SelectItem value="60" className="text-gray-300">60分以上</SelectItem>
              <SelectItem value="0" className="text-gray-300">不限</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 预算范围 */}
        <div>
          <Label className="text-gray-300 mb-2 block">预算范围（万元）</Label>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              value={localFilters.min_budget || ''}
              onChange={(e) =>
                setLocalFilters({
                  ...localFilters,
                  min_budget: parseInt(e.target.value) || undefined,
                })
              }
              placeholder="最小"
              className="bg-gray-700 border-gray-600 text-white"
            />
            <span className="text-gray-500">-</span>
            <Input
              type="number"
              value={localFilters.max_budget || ''}
              onChange={(e) =>
                setLocalFilters({
                  ...localFilters,
                  max_budget: parseInt(e.target.value) || undefined,
                })
              }
              placeholder="最大"
              className="bg-gray-700 border-gray-600 text-white"
            />
          </div>
        </div>

        {/* 排序方式 */}
        <div>
          <Label className="text-gray-300 mb-2 block flex items-center gap-2">
            <ArrowUpDown className="h-4 w-4" />
            排序方式
          </Label>
          <Select
            value={localSort.sort_by || 'match_score'}
            onValueChange={(value: any) =>
              setLocalSort({ ...localSort, sort_by: value })
            }
          >
            <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
              <SelectValue placeholder="选择排序" />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="match_score" className="text-gray-300">匹配度</SelectItem>
              <SelectItem value="budget" className="text-gray-300">预算金额</SelectItem>
              <SelectItem value="deadline" className="text-gray-300">截止时间</SelectItem>
              <SelectItem value="publish_date" className="text-gray-300">发布时间</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 排序顺序 */}
        <div>
          <Label className="text-gray-300 mb-2 block">排序顺序</Label>
          <Select
            value={localSort.order || 'desc'}
            onValueChange={(value: any) =>
              setLocalSort({ ...localSort, order: value })
            }
          >
            <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
              <SelectValue placeholder="选择顺序" />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="desc" className="text-gray-300">降序（高到低）</SelectItem>
              <SelectItem value="asc" className="text-gray-300">升序（低到高）</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 地域筛选 */}
      <div>
        <Label className="text-gray-300 mb-3 block">目标地域（可多选）</Label>
        <div className="flex flex-wrap gap-2">
          {PRESET_AREAS.map((area) => (
            <Badge
              key={area}
              variant={selectedAreas.includes(area) ? 'default' : 'outline'}
              className={`cursor-pointer ${
                selectedAreas.includes(area)
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => toggleArea(area)}
            >
              {area}
              {selectedAreas.includes(area) && <X className="ml-1 h-3 w-3" />}
            </Badge>
          ))}
        </div>
      </div>

      {/* 行业筛选 */}
      <div>
        <Label className="text-gray-300 mb-3 block">目标行业（可多选）</Label>
        <div className="flex flex-wrap gap-2">
          {PRESET_INDUSTRIES.map((industry) => (
            <Badge
              key={industry}
              variant={selectedIndustries.includes(industry) ? 'default' : 'outline'}
              className={`cursor-pointer ${
                selectedIndustries.includes(industry)
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => toggleIndustry(industry)}
            >
              {industry}
              {selectedIndustries.includes(industry) && <X className="ml-1 h-3 w-3" />}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}

