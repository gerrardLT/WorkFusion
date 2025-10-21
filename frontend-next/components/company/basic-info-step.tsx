'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { Company } from '@/types/company';

interface BasicInfoStepProps {
  formData: Partial<Company>;
  updateFormData: (data: Partial<Company>) => void;
}

export default function BasicInfoStep({ formData, updateFormData }: BasicInfoStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">基本信息</h2>
        <p className="text-gray-400 text-sm mb-6">
          请填写企业的基本资料，带 * 的为必填项
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 企业名称 */}
        <div className="md:col-span-2">
          <Label htmlFor="name" className="text-gray-300">
            企业名称 <span className="text-red-500">*</span>
          </Label>
          <Input
            id="name"
            value={formData.name || ''}
            onChange={(e) => updateFormData({ name: e.target.value })}
            placeholder="请输入企业全称"
            className="bg-gray-700 border-gray-600 text-white mt-2"
            required
          />
        </div>

        {/* 企业简介 */}
        <div className="md:col-span-2">
          <Label htmlFor="description" className="text-gray-300">
            企业简介
          </Label>
          <Textarea
            id="description"
            value={formData.description || ''}
            onChange={(e) => updateFormData({ description: e.target.value })}
            placeholder="简要介绍企业主营业务、核心优势等（200字以内）"
            rows={4}
            maxLength={200}
            className="bg-gray-700 border-gray-600 text-white mt-2"
          />
          <div className="text-xs text-gray-500 mt-1 text-right">
            {(formData.description || '').length} / 200
          </div>
        </div>

        {/* 企业规模 */}
        <div>
          <Label htmlFor="scale" className="text-gray-300">
            企业规模 <span className="text-red-500">*</span>
          </Label>
          <Select
            value={formData.scale || 'medium'}
            onValueChange={(value) => updateFormData({ scale: value as 'small' | 'medium' | 'large' })}
          >
            <SelectTrigger className="bg-gray-700 border-gray-600 text-white mt-2">
              <SelectValue placeholder="选择企业规模" />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="small" className="text-gray-300">小型企业（&lt;50人）</SelectItem>
              <SelectItem value="medium" className="text-gray-300">中型企业（50-500人）</SelectItem>
              <SelectItem value="large" className="text-gray-300">大型企业（&gt;500人）</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 员工数量 */}
        <div>
          <Label htmlFor="employee_count" className="text-gray-300">
            员工数量
          </Label>
          <Input
            id="employee_count"
            type="number"
            value={formData.employee_count || ''}
            onChange={(e) => updateFormData({ employee_count: parseInt(e.target.value) || undefined })}
            placeholder="员工总数"
            min="1"
            className="bg-gray-700 border-gray-600 text-white mt-2"
          />
        </div>

        {/* 注册资本 */}
        <div>
          <Label htmlFor="registered_capital" className="text-gray-300">
            注册资本（万元）
          </Label>
          <Input
            id="registered_capital"
            type="number"
            value={formData.registered_capital || ''}
            onChange={(e) => updateFormData({ registered_capital: parseInt(e.target.value) || undefined })}
            placeholder="注册资本"
            min="0"
            className="bg-gray-700 border-gray-600 text-white mt-2"
          />
        </div>

        {/* 成立年份 */}
        <div>
          <Label htmlFor="founded_year" className="text-gray-300">
            成立年份
          </Label>
          <Input
            id="founded_year"
            type="number"
            value={formData.founded_year || ''}
            onChange={(e) => updateFormData({ founded_year: parseInt(e.target.value) || undefined })}
            placeholder="如：2020"
            min="1900"
            max={new Date().getFullYear()}
            className="bg-gray-700 border-gray-600 text-white mt-2"
          />
        </div>
      </div>

      <div className="border-t border-gray-700 pt-6 mt-6">
        <h3 className="text-lg font-semibold text-white mb-4">联系信息</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 联系人 */}
          <div>
            <Label htmlFor="contact_person" className="text-gray-300">
              联系人
            </Label>
            <Input
              id="contact_person"
              value={formData.contact_person || ''}
              onChange={(e) => updateFormData({ contact_person: e.target.value })}
              placeholder="负责人姓名"
              className="bg-gray-700 border-gray-600 text-white mt-2"
            />
          </div>

          {/* 联系电话 */}
          <div>
            <Label htmlFor="contact_phone" className="text-gray-300">
              联系电话
            </Label>
            <Input
              id="contact_phone"
              type="tel"
              value={formData.contact_phone || ''}
              onChange={(e) => updateFormData({ contact_phone: e.target.value })}
              placeholder="手机或座机号码"
              className="bg-gray-700 border-gray-600 text-white mt-2"
            />
          </div>

          {/* 联系邮箱 */}
          <div>
            <Label htmlFor="contact_email" className="text-gray-300">
              联系邮箱
            </Label>
            <Input
              id="contact_email"
              type="email"
              value={formData.contact_email || ''}
              onChange={(e) => updateFormData({ contact_email: e.target.value })}
              placeholder="email@example.com"
              className="bg-gray-700 border-gray-600 text-white mt-2"
            />
          </div>

          {/* 官网 */}
          <div>
            <Label htmlFor="website" className="text-gray-300">
              官方网站
            </Label>
            <Input
              id="website"
              type="url"
              value={formData.website || ''}
              onChange={(e) => updateFormData({ website: e.target.value })}
              placeholder="https://www.example.com"
              className="bg-gray-700 border-gray-600 text-white mt-2"
            />
          </div>

          {/* 地址 */}
          <div className="md:col-span-2">
            <Label htmlFor="address" className="text-gray-300">
              公司地址
            </Label>
            <Input
              id="address"
              value={formData.address || ''}
              onChange={(e) => updateFormData({ address: e.target.value })}
              placeholder="详细地址"
              className="bg-gray-700 border-gray-600 text-white mt-2"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
