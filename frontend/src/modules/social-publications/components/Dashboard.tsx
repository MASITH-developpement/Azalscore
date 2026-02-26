/**
 * AZALSCORE - Dashboard Publications & Leads
 * ==========================================
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart3,
  Send,
  Users,
  Target,
  TrendingUp,
  Calendar,
  PlusCircle,
  ArrowRight,
} from 'lucide-react';

import {
  useCampaigns,
  usePosts,
  useLeadFunnel,
  usePlatformAnalytics,
} from '../api';
import { PLATFORM_OPTIONS } from '../types';

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const { data: campaigns } = useCampaigns({ status: 'active', limit: 5 });
  const { data: recentPosts } = usePosts({ limit: 5 });
  const { data: funnel } = useLeadFunnel();
  const { data: platformStats } = usePlatformAnalytics();

  const totalPublished = recentPosts?.filter(p => p.status === 'published').length || 0;
  const totalScheduled = recentPosts?.filter(p => p.status === 'scheduled').length || 0;
  const totalDrafts = recentPosts?.filter(p => p.status === 'draft').length || 0;

  return (
    <div className="space-y-6">
      {/* KPIs principaux */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Send className="h-4 w-4" />
              Publications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPublished}</div>
            <p className="text-xs text-gray-500">
              {totalScheduled} programmées &middot; {totalDrafts} brouillons
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Users className="h-4 w-4" />
              Leads générés
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {funnel?.total_leads || 0}
            </div>
            <p className="text-xs text-gray-500">
              {funnel?.new || 0} nouveaux cette semaine
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Target className="h-4 w-4" />
              Taux de conversion
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {funnel?.conversion_rate?.toFixed(1) || 0}%
            </div>
            <p className="text-xs text-gray-500">
              {funnel?.won || 0} clients gagnés
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Engagement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {platformStats?.reduce((sum, p) => sum + p.total_engagement, 0)?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-gray-500">
              Likes, commentaires, partages
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Campagnes actives */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Campagnes actives</CardTitle>
            <Button variant="ghost" size="sm">
              Voir tout
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </CardHeader>
          <CardContent>
            {!campaigns || campaigns.length === 0 ? (
              <div className="text-center py-6 text-gray-500">
                <Calendar className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>Aucune campagne active</p>
                <Button variant="link" size="sm">
                  Créer une campagne
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {campaigns.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium">{campaign.name}</div>
                      <div className="text-sm text-gray-500">
                        {campaign.total_posts} posts &middot; {campaign.total_leads} leads
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-green-600">
                        {campaign.total_conversions} conversions
                      </div>
                      {campaign.budget > 0 && (
                        <div className="text-xs text-gray-500">
                          {campaign.actual_spend}€ / {campaign.budget}€
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Performance par plateforme */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Performance par plateforme</CardTitle>
          </CardHeader>
          <CardContent>
            {!platformStats || platformStats.length === 0 ? (
              <div className="text-center py-6 text-gray-500">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>Pas encore de données</p>
                <p className="text-sm">Publiez pour voir vos stats</p>
              </div>
            ) : (
              <div className="space-y-3">
                {platformStats.map((stat) => {
                  const platform = PLATFORM_OPTIONS.find(
                    (p) => p.value === stat.platform
                  );
                  return (
                    <div
                      key={stat.platform}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium">
                          {platform?.label?.charAt(0) || '?'}
                        </span>
                        <div>
                          <div className="font-medium">
                            {platform?.label || stat.platform}
                          </div>
                          <div className="text-xs text-gray-500">
                            {stat.posts_count} posts
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">
                          {stat.total_impressions.toLocaleString()}
                        </div>
                        <div className="text-xs text-gray-500">impressions</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions rapides */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Actions rapides</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Button onClick={() => onNavigate('posts')}>
              <PlusCircle className="h-4 w-4 mr-2" />
              Nouvelle publication
            </Button>
            <Button variant="outline" onClick={() => onNavigate('leads')}>
              <Users className="h-4 w-4 mr-2" />
              Voir les leads
            </Button>
            <Button variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Calendrier éditorial
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
