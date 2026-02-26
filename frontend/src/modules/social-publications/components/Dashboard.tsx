/**
 * AZALSCORE - Dashboard Publications & Leads
 * ==========================================
 * Design premium avec glassmorphism et animations
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  BarChart3,
  Send,
  Users,
  Target,
  TrendingUp,
  Calendar,
  PlusCircle,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  MousePointerClick,
  Heart,
  Share2,
  Sparkles,
  Rocket,
  Trophy,
  Zap,
  Clock,
  CheckCircle2,
  Globe,
  Megaphone,
  BarChart2,
  Activity,
  ChevronRight,
  Play,
  Image,
  MessageCircle,
} from 'lucide-react';

import {
  useCampaigns,
  usePosts,
  useLeadFunnel,
  usePlatformAnalytics,
} from '../api';
import type { MarketingPlatform } from '../types';

// Icônes SVG des plateformes avec couleurs officielles
const platforms = {
  meta_facebook: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
      </svg>
    ),
    color: '#1877F2',
    bg: 'bg-[#1877F2]',
    name: 'Facebook',
  },
  meta_instagram: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073z"/>
      </svg>
    ),
    color: '#E4405F',
    bg: 'bg-gradient-to-br from-[#833AB4] via-[#E4405F] to-[#FCAF45]',
    name: 'Instagram',
  },
  linkedin: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
      </svg>
    ),
    color: '#0A66C2',
    bg: 'bg-[#0A66C2]',
    name: 'LinkedIn',
  },
  twitter: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
      </svg>
    ),
    color: '#000000',
    bg: 'bg-black',
    name: 'X (Twitter)',
  },
  tiktok: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
      </svg>
    ),
    color: '#000000',
    bg: 'bg-black',
    name: 'TikTok',
  },
  youtube: {
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
      </svg>
    ),
    color: '#FF0000',
    bg: 'bg-[#FF0000]',
    name: 'YouTube',
  },
};

// Mini sparkline component
const Sparkline: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((v - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg className="w-full h-8" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

// Circular progress
const CircularProgress: React.FC<{ value: number; size?: number; color?: string }> = ({
  value,
  size = 80,
  color = '#6366f1'
}) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e5e7eb"
        strokeWidth="6"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="6"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-1000"
      />
    </svg>
  );
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
  const totalImpressions = platformStats?.reduce((sum, p) => sum + p.total_impressions, 0) || 0;

  // Fake sparkline data for demo
  const sparklineData = [12, 19, 15, 25, 22, 30, 28, 35, 32, 40];

  return (
    <div className="space-y-8">
      {/* Hero Section avec gradient animé */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-violet-600 via-purple-600 to-fuchsia-500 p-8 md:p-10">
        {/* Cercles décoratifs animés */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 animate-pulse" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-fuchsia-400/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        <div className="absolute top-1/2 left-1/2 w-32 h-32 bg-white/5 rounded-full blur-2xl" />

        {/* Grille de points */}
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }} />

        <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 text-white/90 text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              Centre de commande marketing
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight">
              Publications & Leads
            </h1>
            <p className="text-white/80 text-lg max-w-lg">
              Créez, planifiez et analysez vos publications sur tous vos réseaux sociaux depuis une interface unique.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button
                onClick={() => onNavigate('posts')}
                size="lg"
                className="bg-white text-purple-700 hover:bg-white/90 shadow-xl shadow-purple-900/20 font-semibold"
              >
                <PlusCircle className="w-5 h-5 mr-2" />
                Nouvelle publication
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
              >
                <Play className="w-5 h-5 mr-2" />
                Voir le tutoriel
              </Button>
            </div>
          </div>

          {/* Stats hero */}
          <div className="flex items-center gap-6">
            <div className="hidden lg:block text-center bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <div className="text-4xl font-bold text-white">{funnel?.total_leads || 0}</div>
              <div className="text-white/70 text-sm mt-1">Leads ce mois</div>
              <div className="flex items-center justify-center gap-1 mt-2 text-emerald-300 text-sm font-medium">
                <ArrowUpRight className="w-4 h-4" />
                +24%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* KPIs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Publications */}
        <div className="group relative bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:shadow-blue-500/10 hover:border-blue-200 transition-all duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-500/10 to-transparent rounded-bl-[60px]" />
          <div className="flex items-start justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg shadow-blue-500/30">
              <Send className="w-6 h-6 text-white" />
            </div>
            <span className="inline-flex items-center gap-1 text-emerald-600 text-sm font-semibold bg-emerald-50 px-2 py-1 rounded-full">
              <ArrowUpRight className="w-3 h-3" />
              12%
            </span>
          </div>
          <div className="space-y-1">
            <h3 className="text-3xl font-bold text-gray-900">{totalPublished}</h3>
            <p className="text-gray-500 font-medium">Publications</p>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-gray-500">
                <Clock className="w-4 h-4 text-blue-500" />
                {totalScheduled} programmées
              </span>
              <span className="text-gray-400">{totalDrafts} brouillons</span>
            </div>
          </div>
        </div>

        {/* Leads */}
        <div className="group relative bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:shadow-emerald-500/10 hover:border-emerald-200 transition-all duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-emerald-500/10 to-transparent rounded-bl-[60px]" />
          <div className="flex items-start justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl shadow-lg shadow-emerald-500/30">
              <Users className="w-6 h-6 text-white" />
            </div>
            <div className="w-16">
              <Sparkline data={sparklineData} color="#10b981" />
            </div>
          </div>
          <div className="space-y-1">
            <h3 className="text-3xl font-bold text-gray-900">{funnel?.total_leads || 0}</h3>
            <p className="text-gray-500 font-medium">Leads générés</p>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full" style={{ width: '65%' }} />
              </div>
              <span className="text-sm font-semibold text-gray-700">65%</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">de l'objectif mensuel</p>
          </div>
        </div>

        {/* Conversion */}
        <div className="group relative bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:shadow-amber-500/10 hover:border-amber-200 transition-all duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-amber-500/10 to-transparent rounded-bl-[60px]" />
          <div className="flex items-start justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg shadow-amber-500/30">
              <Target className="w-6 h-6 text-white" />
            </div>
            <div className="relative">
              <CircularProgress value={funnel?.conversion_rate || 0} size={56} color="#f59e0b" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-gray-700">{funnel?.conversion_rate?.toFixed(0) || 0}%</span>
              </div>
            </div>
          </div>
          <div className="space-y-1">
            <h3 className="text-3xl font-bold text-gray-900">{funnel?.won || 0}</h3>
            <p className="text-gray-500 font-medium">Clients gagnés</p>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
            <span className="flex items-center gap-1 text-emerald-600 font-medium text-sm">
              <Trophy className="w-4 h-4" />
              Taux: {funnel?.conversion_rate?.toFixed(1) || 0}%
            </span>
            <span className="text-red-500 text-sm">{funnel?.lost || 0} perdus</span>
          </div>
        </div>

        {/* Engagement */}
        <div className="group relative bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:shadow-purple-500/10 hover:border-purple-200 transition-all duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-purple-500/10 to-transparent rounded-bl-[60px]" />
          <div className="flex items-start justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-xl shadow-lg shadow-purple-500/30">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <Activity className="w-10 h-10 text-purple-200" />
          </div>
          <div className="space-y-1">
            <h3 className="text-3xl font-bold text-gray-900">
              {totalEngagement > 1000 ? `${(totalEngagement / 1000).toFixed(1)}k` : totalEngagement}
            </h3>
            <p className="text-gray-500 font-medium">Engagement total</p>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1 text-red-500">
                <Heart className="w-4 h-4" fill="currentColor" /> Likes
              </span>
              <span className="flex items-center gap-1 text-blue-500">
                <MessageCircle className="w-4 h-4" /> Comments
              </span>
              <span className="flex items-center gap-1 text-green-500">
                <Share2 className="w-4 h-4" /> Shares
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Plateformes & Campagnes */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Performance par plateforme */}
        <div className="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Performance par plateforme</h2>
                <p className="text-sm text-gray-500 mt-1">Statistiques des 30 derniers jours</p>
              </div>
              <Button variant="outline" size="sm" className="text-gray-600">
                <BarChart2 className="w-4 h-4 mr-2" />
                Voir détails
              </Button>
            </div>
          </div>

          <div className="p-6">
            {!platformStats || platformStats.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-gray-100 to-gray-50 rounded-2xl flex items-center justify-center">
                  <Globe className="w-10 h-10 text-gray-300" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Aucune donnée disponible</h3>
                <p className="text-gray-500 text-sm mb-4">Publiez du contenu pour voir vos statistiques</p>
                <Button onClick={() => onNavigate('posts')} className="bg-gradient-to-r from-purple-600 to-fuchsia-600">
                  <PlusCircle className="w-4 h-4 mr-2" />
                  Créer une publication
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {platformStats.map((stat) => {
                  const platform = platforms[stat.platform as keyof typeof platforms];
                  if (!platform) return null;

                  const maxImpressions = Math.max(...platformStats.map(s => s.total_impressions));
                  const percentage = maxImpressions > 0 ? (stat.total_impressions / maxImpressions) * 100 : 0;

                  return (
                    <div
                      key={stat.platform}
                      className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <div className={`w-12 h-12 ${platform.bg} rounded-xl flex items-center justify-center text-white shadow-lg`}>
                        {platform.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold text-gray-900">{platform.name}</span>
                          <span className="text-sm font-medium text-gray-500">{stat.posts_count} posts</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${platform.bg} rounded-full transition-all duration-1000`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="flex items-center gap-6 mt-2 text-sm">
                          <span className="flex items-center gap-1 text-gray-600">
                            <Eye className="w-3.5 h-3.5" />
                            {stat.total_impressions.toLocaleString()}
                          </span>
                          <span className="flex items-center gap-1 text-gray-600">
                            <MousePointerClick className="w-3.5 h-3.5" />
                            {stat.total_clicks.toLocaleString()}
                          </span>
                          <span className="flex items-center gap-1 text-emerald-600 font-medium">
                            <Users className="w-3.5 h-3.5" />
                            {stat.leads_generated} leads
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-300" />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Campagnes actives */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Campagnes actives</h2>
                <p className="text-sm text-gray-500 mt-1">{campaigns?.length || 0} en cours</p>
              </div>
              <Button variant="ghost" size="sm" className="text-purple-600 hover:text-purple-700 hover:bg-purple-50">
                <PlusCircle className="w-4 h-4 mr-1" />
                Créer
              </Button>
            </div>
          </div>

          <div className="p-6">
            {!campaigns || campaigns.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-orange-100 to-amber-50 rounded-2xl flex items-center justify-center">
                  <Megaphone className="w-8 h-8 text-orange-400" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Aucune campagne</h3>
                <p className="text-gray-500 text-sm mb-4">Lancez votre première campagne marketing</p>
                <Button variant="outline" size="sm">
                  Créer une campagne
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {campaigns.map((campaign) => {
                  const progress = campaign.budget > 0 ? (campaign.actual_spend / campaign.budget) * 100 : 0;

                  return (
                    <div
                      key={campaign.id}
                      className="p-4 rounded-xl border border-gray-100 hover:border-purple-200 hover:shadow-md transition-all cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-gray-900">{campaign.name}</h4>
                          <p className="text-sm text-gray-500 mt-0.5">
                            {campaign.total_posts} posts · {campaign.total_leads} leads
                          </p>
                        </div>
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">
                          {campaign.total_conversions} conv.
                        </span>
                      </div>

                      {campaign.budget > 0 && (
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1.5">
                            <span className="text-gray-500">Budget</span>
                            <span className="font-medium text-gray-700">
                              {campaign.actual_spend}€ / {campaign.budget}€
                            </span>
                          </div>
                          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                progress > 80 ? 'bg-red-500' : progress > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${Math.min(progress, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Actions rapides */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-8 text-white">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <h2 className="text-xl font-bold mb-2">Prêt à développer votre audience ?</h2>
            <p className="text-gray-400">Créez du contenu engageant et convertissez vos visiteurs en clients.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() => onNavigate('posts')}
              size="lg"
              className="bg-gradient-to-r from-purple-500 to-fuchsia-500 hover:from-purple-600 hover:to-fuchsia-600 shadow-lg shadow-purple-500/25"
            >
              <PlusCircle className="w-5 h-5 mr-2" />
              Nouvelle publication
            </Button>
            <Button
              onClick={() => onNavigate('leads')}
              variant="outline"
              size="lg"
              className="border-gray-600 text-white hover:bg-white/10"
            >
              <Users className="w-5 h-5 mr-2" />
              Voir les leads
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-gray-600 text-white hover:bg-white/10"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Suggestions IA
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
