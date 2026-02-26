/**
 * AZALSCORE - Dashboard Publications & Leads
 * ==========================================
 * Design professionnel avec icônes et visuels engageants
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  BarChart3,
  Send,
  Users,
  Target,
  TrendingUp,
  Calendar,
  PlusCircle,
  ArrowRight,
  Eye,
  MousePointerClick,
  Heart,
  Share2,
  Sparkles,
  Rocket,
  Trophy,
  Zap,
} from 'lucide-react';

import {
  useCampaigns,
  usePosts,
  useLeadFunnel,
  usePlatformAnalytics,
} from '../api';
import type { MarketingPlatform } from '../types';

// Icônes SVG des plateformes sociales
const PlatformIcons: Record<string, React.FC<{ className?: string }>> = {
  meta_facebook: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  ),
  meta_instagram: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
    </svg>
  ),
  linkedin: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  ),
  twitter: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
    </svg>
  ),
  tiktok: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
    </svg>
  ),
  youtube: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
    </svg>
  ),
};

const platformColors: Record<string, { bg: string; text: string; border: string }> = {
  meta_facebook: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200' },
  meta_instagram: { bg: 'bg-gradient-to-br from-purple-50 to-pink-50', text: 'text-pink-600', border: 'border-pink-200' },
  linkedin: { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200' },
  twitter: { bg: 'bg-slate-50', text: 'text-slate-800', border: 'border-slate-200' },
  tiktok: { bg: 'bg-slate-50', text: 'text-slate-900', border: 'border-slate-200' },
  youtube: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' },
};

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const { data: campaigns } = useCampaigns({ status: 'active', limit: 5 });
  const { data: recentPosts } = usePosts({ limit: 10 });
  const { data: funnel } = useLeadFunnel();
  const { data: platformStats } = usePlatformAnalytics();

  const totalPublished = recentPosts?.filter(p => p.status === 'published').length || 0;
  const totalScheduled = recentPosts?.filter(p => p.status === 'scheduled').length || 0;
  const totalDrafts = recentPosts?.filter(p => p.status === 'draft').length || 0;
  const totalEngagement = platformStats?.reduce((sum, p) => sum + p.total_engagement, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 p-8 text-white">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIxLTEuNzktNC00LTRzLTQgMS43OS00IDQgMS43OSA0IDQgNCA0LTEuNzkgNC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
              <Rocket className="h-8 w-8" />
              Centre de Publication
            </h1>
            <p className="text-white/80 text-lg">
              Gérez vos réseaux sociaux et convertissez vos visiteurs en clients
            </p>
          </div>
          <div className="hidden md:flex items-center gap-3">
            <Button
              onClick={() => onNavigate('posts')}
              className="bg-white text-purple-600 hover:bg-white/90 shadow-lg"
            >
              <PlusCircle className="h-4 w-4 mr-2" />
              Nouvelle publication
            </Button>
          </div>
        </div>
      </div>

      {/* KPIs avec design moderne */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-bl-full" />
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <Send className="h-6 w-6 text-blue-600" />
              </div>
              <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                Ce mois
              </span>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-gray-900">{totalPublished}</p>
              <p className="text-sm text-gray-500">Publications</p>
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-blue-400 rounded-full" />
                {totalScheduled} programmées
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-300 rounded-full" />
                {totalDrafts} brouillons
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 rounded-bl-full" />
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-emerald-100 rounded-xl">
                <Users className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="flex items-center gap-1 text-emerald-600">
                <TrendingUp className="h-3 w-3" />
                <span className="text-xs font-medium">+12%</span>
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-gray-900">{funnel?.total_leads || 0}</p>
              <p className="text-sm text-gray-500">Leads générés</p>
            </div>
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-gray-500">Objectif mensuel</span>
                <span className="font-medium">75%</span>
              </div>
              <Progress value={75} className="h-1.5" />
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-bl-full" />
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-amber-100 rounded-xl">
                <Target className="h-6 w-6 text-amber-600" />
              </div>
              <Trophy className="h-5 w-5 text-amber-500" />
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-gray-900">
                {funnel?.conversion_rate?.toFixed(1) || 0}%
              </p>
              <p className="text-sm text-gray-500">Taux de conversion</p>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <span className="text-2xl">🎯</span>
              <span className="text-sm text-gray-600">
                <span className="font-semibold text-emerald-600">{funnel?.won || 0}</span> clients gagnés
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-purple-500/10 to-purple-500/5 rounded-bl-full" />
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 rounded-xl">
                <Zap className="h-6 w-6 text-purple-600" />
              </div>
              <Sparkles className="h-5 w-5 text-purple-500" />
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-gray-900">
                {totalEngagement.toLocaleString()}
              </p>
              <p className="text-sm text-gray-500">Engagement total</p>
            </div>
            <div className="mt-4 flex items-center gap-3 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Heart className="h-3 w-3 text-red-400" /> Likes
              </span>
              <span className="flex items-center gap-1">
                <Share2 className="h-3 w-3 text-blue-400" /> Partages
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance par plateforme */}
        <Card className="lg:col-span-2 border-0 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-indigo-500" />
                Performance par plateforme
              </CardTitle>
              <Button variant="ghost" size="sm" className="text-indigo-600">
                Détails <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {!platformStats || platformStats.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
                  <TrendingUp className="h-8 w-8 text-indigo-400" />
                </div>
                <p className="text-gray-600 font-medium mb-1">Pas encore de données</p>
                <p className="text-sm text-gray-400">Publiez du contenu pour voir vos statistiques</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => onNavigate('posts')}
                >
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Créer une publication
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {platformStats.map((stat) => {
                  const Icon = PlatformIcons[stat.platform];
                  const colors = platformColors[stat.platform] || { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' };
                  const maxImpressions = Math.max(...platformStats.map(s => s.total_impressions));
                  const percentage = maxImpressions > 0 ? (stat.total_impressions / maxImpressions) * 100 : 0;

                  return (
                    <div
                      key={stat.platform}
                      className={`p-4 rounded-xl border ${colors.border} ${colors.bg} hover:shadow-sm transition-shadow`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colors.text} bg-white shadow-sm`}>
                          {Icon ? <Icon className="w-6 h-6" /> : <span className="text-lg font-bold">?</span>}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-gray-900 capitalize">
                              {stat.platform.replace('meta_', '').replace('_', ' ')}
                            </span>
                            <span className="text-sm font-medium text-gray-600">
                              {stat.posts_count} posts
                            </span>
                          </div>
                          <div className="relative h-2 bg-white rounded-full overflow-hidden">
                            <div
                              className={`absolute inset-y-0 left-0 rounded-full ${colors.text.replace('text-', 'bg-')}`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                            <div className="flex items-center gap-3">
                              <span className="flex items-center gap-1">
                                <Eye className="h-3 w-3" />
                                {stat.total_impressions.toLocaleString()}
                              </span>
                              <span className="flex items-center gap-1">
                                <MousePointerClick className="h-3 w-3" />
                                {stat.total_clicks.toLocaleString()}
                              </span>
                            </div>
                            <span className="text-emerald-600 font-medium">
                              {stat.leads_generated} leads
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Campagnes actives */}
        <Card className="border-0 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Calendar className="h-5 w-5 text-orange-500" />
                Campagnes actives
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {!campaigns || campaigns.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-14 h-14 mx-auto mb-3 bg-gradient-to-br from-orange-100 to-amber-100 rounded-2xl flex items-center justify-center">
                  <Rocket className="h-7 w-7 text-orange-400" />
                </div>
                <p className="text-gray-600 font-medium mb-1">Aucune campagne</p>
                <p className="text-sm text-gray-400 mb-4">Lancez votre première campagne</p>
                <Button variant="outline" size="sm">
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Créer
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {campaigns.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="p-4 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-100 hover:border-orange-200 hover:shadow-sm transition-all cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-gray-900 text-sm">{campaign.name}</h4>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {campaign.total_posts} posts · {campaign.total_leads} leads
                        </p>
                      </div>
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                        {campaign.total_conversions} conv.
                      </span>
                    </div>
                    {campaign.budget > 0 && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-500">Budget utilisé</span>
                          <span className="font-medium">{Math.round((campaign.actual_spend / campaign.budget) * 100)}%</span>
                        </div>
                        <Progress value={(campaign.actual_spend / campaign.budget) * 100} className="h-1" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions rapides */}
      <Card className="border-0 shadow-md bg-gradient-to-r from-slate-50 to-white">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center gap-4">
            <Button
              onClick={() => onNavigate('posts')}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md"
            >
              <PlusCircle className="h-4 w-4 mr-2" />
              Nouvelle publication
            </Button>
            <Button
              variant="outline"
              onClick={() => onNavigate('leads')}
              className="border-emerald-200 text-emerald-700 hover:bg-emerald-50"
            >
              <Users className="h-4 w-4 mr-2" />
              Gérer les leads
            </Button>
            <Button variant="outline" className="border-blue-200 text-blue-700 hover:bg-blue-50">
              <Calendar className="h-4 w-4 mr-2" />
              Calendrier éditorial
            </Button>
            <Button variant="outline" className="border-purple-200 text-purple-700 hover:bg-purple-50">
              <Sparkles className="h-4 w-4 mr-2" />
              Suggestions IA
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
