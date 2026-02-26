/**
 * AZALSCORE - Module Publications Réseaux Sociaux
 * ================================================
 * Interface moderne pour la gestion des publications et leads
 */

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LayoutDashboard, Send, Users } from 'lucide-react';

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex items-center justify-between mb-6">
            <TabsList className="bg-white shadow-sm border border-gray-100 p-1 rounded-xl">
              <TabsTrigger
                value="dashboard"
                className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg px-4 py-2"
              >
                <LayoutDashboard className="h-4 w-4" />
                Tableau de bord
              </TabsTrigger>
              <TabsTrigger
                value="posts"
                className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg px-4 py-2"
              >
                <Send className="h-4 w-4" />
                Publications
              </TabsTrigger>
              <TabsTrigger
                value="leads"
                className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg px-4 py-2"
              >
                <Users className="h-4 w-4" />
                Leads
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="dashboard" className="mt-0 focus-visible:outline-none">
            <Dashboard onNavigate={setActiveTab} />
          </TabsContent>

          <TabsContent value="posts" className="mt-0 focus-visible:outline-none">
            <PostsList />
          </TabsContent>

          <TabsContent value="leads" className="mt-0 focus-visible:outline-none">
            <LeadsList />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export { SocialPublicationsModule };
