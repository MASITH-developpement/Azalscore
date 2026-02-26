/**
 * AZALSCORE - Module Publications Réseaux Sociaux
 * ================================================
 */

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Composants
import { Dashboard } from './components/Dashboard';
import { PostsList } from './components/PostsList';
import { LeadsList } from './components/LeadsList';

/**
 * Module Principal - Publications & Leads Réseaux Sociaux
 */
export default function SocialPublicationsModule() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Publications & Leads</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="dashboard">Tableau de bord</TabsTrigger>
          <TabsTrigger value="posts">Publications</TabsTrigger>
          <TabsTrigger value="leads">Leads</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="mt-4">
          <Dashboard onNavigate={setActiveTab} />
        </TabsContent>

        <TabsContent value="posts" className="mt-4">
          <PostsList />
        </TabsContent>

        <TabsContent value="leads" className="mt-4">
          <LeadsList />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export { SocialPublicationsModule };
