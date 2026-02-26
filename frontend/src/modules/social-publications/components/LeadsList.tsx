/**
 * AZALSCORE - Liste des Leads
 * ============================
 * Design professionnel avec pipeline visuel et actions rapides
 */

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import {
  Search,
  MoreVertical,
  Mail,
  Phone,
  Building2,
  MessageSquare,
  UserCheck,
  TrendingUp,
  Users,
  Target,
  Sparkles,
  ExternalLink,
  Plus,
  RefreshCw,
  Trophy,
  Loader2,
  Star,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import {
  useLeads,
  useLeadFunnel,
  useUpdateLead,
  useConvertLead,
} from '../api';
import type { SocialLead, LeadStatus, LeadSource } from '../types';
import { LEAD_STATUS_OPTIONS } from '../types';

// Icônes des sources
const sourceIcons: Record<LeadSource, React.FC<{ className?: string }>> = {
  facebook: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  ),
  instagram: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073z"/>
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
  google_ads: ({ className }) => <Target className={className} />,
  website: ({ className }) => <ExternalLink className={className} />,
  referral: ({ className }) => <Users className={className} />,
  organic: ({ className }) => <TrendingUp className={className} />,
  other: ({ className }) => <Sparkles className={className} />,
};

const sourceColors: Record<LeadSource, string> = {
  facebook: 'text-blue-600 bg-blue-50',
  instagram: 'text-pink-600 bg-pink-50',
  linkedin: 'text-sky-700 bg-sky-50',
  twitter: 'text-slate-800 bg-slate-100',
  google_ads: 'text-green-600 bg-green-50',
  website: 'text-indigo-600 bg-indigo-50',
  referral: 'text-amber-600 bg-amber-50',
  organic: 'text-emerald-600 bg-emerald-50',
  other: 'text-gray-600 bg-gray-100',
};

const statusConfig: Record<LeadStatus, { color: string; bg: string; progress: number }> = {
  new: { color: 'text-blue-600', bg: 'bg-blue-100', progress: 10 },
  contacted: { color: 'text-cyan-600', bg: 'bg-cyan-100', progress: 25 },
  qualified: { color: 'text-purple-600', bg: 'bg-purple-100', progress: 45 },
  proposal: { color: 'text-orange-600', bg: 'bg-orange-100', progress: 60 },
  negotiation: { color: 'text-amber-600', bg: 'bg-amber-100', progress: 80 },
  won: { color: 'text-emerald-600', bg: 'bg-emerald-100', progress: 100 },
  lost: { color: 'text-red-600', bg: 'bg-red-100', progress: 0 },
  nurturing: { color: 'text-gray-600', bg: 'bg-gray-100', progress: 15 },
};

export function LeadsList() {
  const [statusFilter, setStatusFilter] = useState<LeadStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLead, setSelectedLead] = useState<SocialLead | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const { data: leads, isLoading } = useLeads({
    status: statusFilter === 'all' ? undefined : statusFilter,
    limit: 100,
  });
  const { data: funnel } = useLeadFunnel();
  const updateLead = useUpdateLead();
  const convertLead = useConvertLead();

  const filteredLeads = leads?.filter((lead) => {
    const searchLower = searchTerm.toLowerCase();
    return (
      lead.first_name?.toLowerCase().includes(searchLower) ||
      lead.last_name?.toLowerCase().includes(searchLower) ||
      lead.email?.toLowerCase().includes(searchLower) ||
      lead.company?.toLowerCase().includes(searchLower)
    );
  });

  const handleStatusChange = async (lead: SocialLead, newStatus: LeadStatus) => {
    await updateLead.mutateAsync({ id: lead.id, data: { status: newStatus } });
  };

  const handleConvert = async (lead: SocialLead) => {
    if (confirm('Convertir ce lead en contact CRM ?')) {
      await convertLead.mutateAsync({ id: lead.id, create_opportunity: true });
    }
  };

  const getInitials = (lead: SocialLead) => {
    const first = lead.first_name?.charAt(0) || '';
    const last = lead.last_name?.charAt(0) || '';
    return (first + last).toUpperCase() || '?';
  };

  const getFullName = (lead: SocialLead) => {
    const parts = [lead.first_name, lead.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(' ') : 'Contact inconnu';
  };

  return (
    <div className="space-y-6">
      {/* Pipeline visuel */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {LEAD_STATUS_OPTIONS.filter(s => s.value !== 'nurturing').map((status) => {
          const config = statusConfig[status.value as LeadStatus];
          const count = funnel?.[status.value as keyof typeof funnel] || 0;
          const isActive = statusFilter === status.value;

          return (
            <button
              key={status.value}
              onClick={() => setStatusFilter(isActive ? 'all' : status.value as LeadStatus)}
              className={`p-4 rounded-xl border-2 transition-all ${
                isActive
                  ? `${config.bg} border-current ${config.color}`
                  : 'bg-white border-gray-100 hover:border-gray-200'
              }`}
            >
              <div className={`text-2xl font-bold ${isActive ? config.color : 'text-gray-900'}`}>
                {typeof count === 'number' ? count : 0}
              </div>
              <div className={`text-xs font-medium ${isActive ? config.color : 'text-gray-500'}`}>
                {status.label}
              </div>
            </button>
          );
        })}
      </div>

      {/* Stats rapides */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-emerald-50 to-white">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600 font-medium mb-1">Taux de conversion</p>
                <p className="text-3xl font-bold text-emerald-700">
                  {funnel?.conversion_rate?.toFixed(1) || 0}%
                </p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-xl">
                <Trophy className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
            <Progress value={funnel?.conversion_rate || 0} className="mt-3 h-1.5" />
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-white">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium mb-1">Total leads</p>
                <p className="text-3xl font-bold text-blue-700">
                  {funnel?.total_leads || 0}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-xl">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <p className="text-xs text-blue-500 mt-2">
              +{funnel?.new || 0} nouveaux cette semaine
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-amber-50 to-white">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600 font-medium mb-1">Clients gagnés</p>
                <p className="text-3xl font-bold text-amber-700">
                  {funnel?.won || 0}
                </p>
              </div>
              <div className="p-3 bg-amber-100 rounded-xl">
                <Star className="h-6 w-6 text-amber-600" />
              </div>
            </div>
            <p className="text-xs text-amber-500 mt-2">
              {funnel?.lost || 0} perdus
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 w-full sm:w-auto">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher un lead..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white"
            />
          </div>
          <Button variant="outline" size="icon" className="shrink-0">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <Button className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md">
          <Plus className="h-4 w-4 mr-2" />
          Ajouter un lead
        </Button>
      </div>

      {/* Liste des leads */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <Loader2 className="h-10 w-10 animate-spin text-indigo-500 mx-auto mb-4" />
            <p className="text-gray-500">Chargement des leads...</p>
          </div>
        </div>
      ) : filteredLeads?.length === 0 ? (
        <Card className="border-dashed border-2 border-gray-200 bg-gradient-to-br from-gray-50 to-white">
          <CardContent className="py-16">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
                <Users className="h-10 w-10 text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Aucun lead trouvé
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Les leads générés par vos publications apparaîtront ici.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredLeads?.map((lead) => {
            const status = statusConfig[lead.status];
            const SourceIcon = sourceIcons[lead.source];
            const sourceColor = sourceColors[lead.source];

            return (
              <Card
                key={lead.id}
                className="border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => {
                  setSelectedLead(lead);
                  setIsDetailOpen(true);
                }}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    {/* Avatar */}
                    <Avatar className="h-12 w-12 border-2 border-white shadow-sm">
                      <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-500 text-white font-semibold">
                        {getInitials(lead)}
                      </AvatarFallback>
                    </Avatar>

                    {/* Info principale */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {getFullName(lead)}
                        </h3>
                        {lead.score >= 70 && (
                          <span className="text-amber-500" title="Lead chaud">
                            🔥
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        {lead.company && (
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3.5 w-3.5" />
                            {lead.company}
                          </span>
                        )}
                        {lead.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="h-3.5 w-3.5" />
                            {lead.email}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Source */}
                    <div className={`p-2 rounded-lg ${sourceColor}`} title={lead.source}>
                      {SourceIcon && <SourceIcon className="h-4 w-4" />}
                    </div>

                    {/* Score */}
                    <div className="text-center px-3">
                      <div className="text-lg font-bold text-gray-900">{lead.score}</div>
                      <div className="text-xs text-gray-500">Score</div>
                    </div>

                    {/* Statut */}
                    <Select
                      value={lead.status}
                      onValueChange={(v) => {
                        handleStatusChange(lead, v as LeadStatus);
                      }}
                    >
                      <SelectTrigger
                        className={`w-[140px] ${status.bg} ${status.color} border-0`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LEAD_STATUS_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    {/* Actions */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={(e) => e.stopPropagation()}>
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Mail className="h-4 w-4 mr-2" />
                          Envoyer un email
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Phone className="h-4 w-4 mr-2" />
                          Appeler
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Ajouter une note
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            handleConvert(lead);
                          }}
                          className="text-emerald-600"
                        >
                          <UserCheck className="h-4 w-4 mr-2" />
                          Convertir en contact
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Date */}
                    <div className="text-xs text-gray-400 w-24 text-right">
                      {formatDistanceToNow(new Date(lead.created_at), {
                        addSuffix: true,
                        locale: fr,
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Dialog détail lead */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-2xl">
          {selectedLead && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-500 text-white">
                      {getInitials(selectedLead)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-semibold">{getFullName(selectedLead)}</div>
                    <div className="text-sm text-gray-500 font-normal">
                      {selectedLead.company || selectedLead.email || 'Sans entreprise'}
                    </div>
                  </div>
                </DialogTitle>
              </DialogHeader>

              <div className="grid grid-cols-2 gap-6 py-4">
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Email</label>
                    <p className="font-medium">{selectedLead.email || '-'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Téléphone</label>
                    <p className="font-medium">{selectedLead.phone || '-'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Entreprise</label>
                    <p className="font-medium">{selectedLead.company || '-'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Poste</label>
                    <p className="font-medium">{selectedLead.job_title || '-'}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Source</label>
                    <p className="font-medium capitalize">{selectedLead.source.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Score</label>
                    <div className="flex items-center gap-2">
                      <Progress value={selectedLead.score} className="h-2 flex-1" />
                      <span className="font-bold">{selectedLead.score}/100</span>
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Intérêt</label>
                    <p className="font-medium">{selectedLead.interest || '-'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wide">Budget</label>
                    <p className="font-medium">{selectedLead.budget_range || '-'}</p>
                  </div>
                </div>
              </div>

              {selectedLead.notes && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <label className="text-xs text-gray-500 uppercase tracking-wide">Notes</label>
                  <p className="text-sm mt-1">{selectedLead.notes}</p>
                </div>
              )}

              <DialogFooter className="gap-2">
                <Button variant="outline">
                  <Mail className="h-4 w-4 mr-2" />
                  Email
                </Button>
                <Button variant="outline">
                  <Phone className="h-4 w-4 mr-2" />
                  Appeler
                </Button>
                <Button
                  className="bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => handleConvert(selectedLead)}
                >
                  <UserCheck className="h-4 w-4 mr-2" />
                  Convertir en contact
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
