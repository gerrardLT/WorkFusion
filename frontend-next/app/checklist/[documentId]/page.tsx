"use client";

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChecklistPanel } from '@/components/checklist/checklist-panel';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function ChecklistPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.documentId as string;

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 返回按钮 */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="text-white hover:bg-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回
          </Button>
        </div>

        {/* Checklist面板 */}
        <ChecklistPanel documentId={documentId} />
      </div>
    </div>
  );
}

