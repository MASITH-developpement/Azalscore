/**
 * AZALSCORE - Liste des Leads
 * ===========================
 */

import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Plus,
  MoreHorizontal,
  Mail,
  Phone,
  UserCheck,
  Trash2,
  Search,
  Filter,
  TrendingUp,
  Users,
  Target,
  CheckCircle,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

import {
  useLeads,
  useLeadFunnel,
  useDeleteLead,
  useUpdateLead,
  useConvertLead,
} from '../api';
import type { SocialLead, LeadStatus } from '../types';
import { LEAD_STATUS_OPTIONS } from '../types';

const getStatusColor = (status: LeadStatus) => {
  const colors: Record<LeadStatus, string> = {
    new: 'bg-blue-100 text-blue-800',
    contacted: 'bg-cyan-100 text-cyan-800',
    qualified: 'bg-purple-100 text-purple-800',
    proposal: 'bg-orange-100 text-orange-800',
    negotiation: 'bg-yellow-100 text-yellow-800',
    won: 'bg-green-100 text-green-800',
    lost: 'bg-red-100 text-red-800',
    nurturing: 'bg-gray-100 text-gray-800',
  };
  return colors[status] || 'bg-gray-100';
};

const getScoreColor = (score: number) => {
  if (score >= 70) return 'text-green-600';
  if (score >= 40) return 'text-yellow-600';
  return 'text-gray-400';
};

export function LeadsList() {
  const [statusFilter, setStatusFilter] = useState<LeadStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const { data: leads, isLoading } = useLeads({
    status: statusFilter === 'all' ? undefined : statusFilter,
    search: searchTerm || undefined,
    limit: 50,
  });

  const { data: funnel } = useLeadFunnel();
  const deleteLead = useDeleteLead();
  const updateLead = useUpdateLead();
  const convertLead = useConvertLead();

  const handleStatusChange = async (lead: SocialLead, newStatus: LeadStatus) => {
    await updateLead.mutateAsync({
      id: lead.id,
      data: { status: newStatus },
    });
  };

  const handleConvert = async (lead: SocialLead) => {
    if (confirm('Convertir ce lead en contact ?')) {
      await convertLead.mutateAsync({
        id: lead.id,
        create_contact: true,
        create_opportunity: true,
      });
    }
  };

  const handleDelete = async (lead: SocialLead) => {
    if (confirm('Supprimer ce lead ?')) {
      await deleteLead.mutateAsync(lead.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Funnel KPIs */}
      {funnel && (
        <div className="grid grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <Users className="h-4 w-4" />
                Total Leads
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{funnel.total_leads}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Qualifiés
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">
                {funnel.qualified}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Gagnés
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{funnel.won}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Taux Conversion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {funnel.conversion_rate.toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher email, nom, entreprise..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as LeadStatus | 'all')}
          >
            <SelectTrigger className="w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Statut" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              {LEAD_STATUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Chargement...</div>
      ) : leads?.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          Aucun lead trouvé.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Contact</TableHead>
              <TableHead>Entreprise</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Créé</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {leads?.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell>
                  <div className="space-y-1">
                    <div className="font-medium">
                      {lead.first_name} {lead.last_name}
                    </div>
                    {lead.email && (
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Mail className="h-3 w-3" />
                        {lead.email}
                      </div>
                    )}
                    {lead.phone && (
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Phone className="h-3 w-3" />
                        {lead.phone}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    {lead.company && (
                      <div className="font-medium">{lead.company}</div>
                    )}
                    {lead.job_title && (
                      <div className="text-sm text-gray-500">{lead.job_title}</div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <Badge variant="outline">
                      {lead.source.replace('_', ' ')}
                    </Badge>
                    {lead.utm_campaign && (
                      <div className="text-xs text-gray-400">
                        {lead.utm_campaign}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className={`text-lg font-bold ${getScoreColor(lead.score)}`}>
                    {lead.score}
                  </div>
                </TableCell>
                <TableCell>
                  <Select
                    value={lead.status}
                    onValueChange={(v) => handleStatusChange(lead, v as LeadStatus)}
                  >
                    <SelectTrigger className="w-[140px] h-8">
                      <Badge className={getStatusColor(lead.status)}>
                        {LEAD_STATUS_OPTIONS.find((o) => o.value === lead.status)?.label}
                      </Badge>
                    </SelectTrigger>
                    <SelectContent>
                      {LEAD_STATUS_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          <Badge className={getStatusColor(opt.value as LeadStatus)}>
                            {opt.label}
                          </Badge>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <div className="text-sm text-gray-500">
                    {formatDistanceToNow(new Date(lead.created_at), {
                      addSuffix: true,
                      locale: fr,
                    })}
                  </div>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {lead.email && (
                        <DropdownMenuItem asChild>
                          <a href={`mailto:${lead.email}`}>
                            <Mail className="h-4 w-4 mr-2" />
                            Envoyer un email
                          </a>
                        </DropdownMenuItem>
                      )}
                      {lead.phone && (
                        <DropdownMenuItem asChild>
                          <a href={`tel:${lead.phone}`}>
                            <Phone className="h-4 w-4 mr-2" />
                            Appeler
                          </a>
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => handleConvert(lead)}>
                        <UserCheck className="h-4 w-4 mr-2" />
                        Convertir en client
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => handleDelete(lead)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Supprimer
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
