/**
 * AZALSCORE - Éditeur de Publication
 * ===================================
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Calendar as CalendarIcon,
  Clock,
  Link as LinkIcon,
  Image,
  Hash,
  Send,
  Save,
  Sparkles,
  Eye,
} from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

import {
  useCreatePost,
  useUpdatePost,
  useSchedulePost,
  usePublishPost,
  useCampaigns,
  useTemplates,
  useRenderTemplate,
  useOptimalTime,
} from '../api';
import type {
  SocialPost,
  PostCreate,
  PostType,
  MarketingPlatform,
} from '../types';
import { PLATFORM_OPTIONS, POST_TYPE_OPTIONS } from '../types';

interface PostEditorProps {
  post?: SocialPost | null;
  onClose: () => void;
}

export function PostEditor({ post, onClose }: PostEditorProps) {
  const [title, setTitle] = useState(post?.title || '');
  const [content, setContent] = useState(post?.content || '');
  const [postType, setPostType] = useState<PostType>(post?.post_type || 'text');
  const [platforms, setPlatforms] = useState<MarketingPlatform[]>(
    post?.platforms || ['meta_facebook', 'linkedin']
  );
  const [linkUrl, setLinkUrl] = useState(post?.link_url || 'https://azalscore.com');
  const [hashtags, setHashtags] = useState(post?.hashtags?.join(' ') || '');
  const [campaignId, setCampaignId] = useState(post?.campaign_id || '');
  const [scheduledDate, setScheduledDate] = useState<Date | undefined>(
    post?.scheduled_at ? new Date(post.scheduled_at) : undefined
  );
  const [scheduledTime, setScheduledTime] = useState(
    post?.scheduled_at
      ? format(new Date(post.scheduled_at), 'HH:mm')
      : '12:00'
  );
  const [selectedTemplateId, setSelectedTemplateId] = useState('');

  const createPost = useCreatePost();
  const updatePost = useUpdatePost();
  const schedulePost = useSchedulePost();
  const publishPost = usePublishPost();
  const renderTemplate = useRenderTemplate();

  const { data: campaigns } = useCampaigns({ status: 'active' });
  const { data: templates } = useTemplates({ active_only: true });
  const { data: optimalTime } = useOptimalTime(platforms[0], scheduledDate?.toISOString().split('T')[0]);

  const characterCount = content.length;
  const maxChars: Record<string, number> = {
    meta_facebook: 63206,
    meta_instagram: 2200,
    linkedin: 3000,
    twitter: 280,
    tiktok: 2200,
  };

  const getCharLimit = () => {
    let min = Infinity;
    for (const p of platforms) {
      if (maxChars[p] && maxChars[p] < min) {
        min = maxChars[p];
      }
    }
    return min === Infinity ? 5000 : min;
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplateId) return;

    try {
      const result = await renderTemplate.mutateAsync({
        id: selectedTemplateId,
        variables: {},
        platforms,
      });
      setContent(result.content);
      setHashtags(result.hashtags.join(' '));
    } catch (error) {
      console.error('Erreur rendu template:', error);
    }
  };

  const handleApplyOptimalTime = () => {
    if (optimalTime?.suggested_datetime) {
      const date = new Date(optimalTime.suggested_datetime);
      setScheduledDate(date);
      setScheduledTime(format(date, 'HH:mm'));
    }
  };

  const buildPostData = (): PostCreate => ({
    title: title || undefined,
    content,
    post_type: postType,
    platforms,
    link_url: linkUrl || undefined,
    hashtags: hashtags.split(/\s+/).filter((h) => h.startsWith('#') || h.length > 0).map((h) => h.startsWith('#') ? h : `#${h}`),
    campaign_id: campaignId || undefined,
    utm_source: 'social',
    utm_medium: 'organic',
    utm_campaign: campaignId ? campaigns?.find(c => c.id === campaignId)?.utm_campaign : undefined,
  });

  const handleSaveDraft = async () => {
    try {
      if (post) {
        await updatePost.mutateAsync({ id: post.id, data: buildPostData() });
      } else {
        await createPost.mutateAsync(buildPostData());
      }
      onClose();
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const handleSchedule = async () => {
    if (!scheduledDate) return;

    try {
      const data = buildPostData();

      // Combiner date et heure
      const [hours, minutes] = scheduledTime.split(':').map(Number);
      const scheduled = new Date(scheduledDate);
      scheduled.setHours(hours, minutes, 0, 0);

      if (post) {
        await updatePost.mutateAsync({ id: post.id, data });
        await schedulePost.mutateAsync({
          id: post.id,
          scheduled_at: scheduled.toISOString(),
          platforms,
        });
      } else {
        const newPost = await createPost.mutateAsync({
          ...data,
          scheduled_at: scheduled.toISOString(),
        });
      }
      onClose();
    } catch (error) {
      console.error('Erreur programmation:', error);
    }
  };

  const handlePublishNow = async () => {
    if (!confirm('Publier maintenant sur ' + platforms.length + ' plateforme(s) ?')) return;

    try {
      if (post) {
        await publishPost.mutateAsync({ id: post.id, platforms });
      } else {
        const newPost = await createPost.mutateAsync(buildPostData());
        await publishPost.mutateAsync({ id: newPost.id, platforms });
      }
      onClose();
    } catch (error) {
      console.error('Erreur publication:', error);
    }
  };

  const isValid = content.length > 0 && platforms.length > 0;

  return (
    <div className="space-y-6">
      <Tabs defaultValue="content">
        <TabsList>
          <TabsTrigger value="content">Contenu</TabsTrigger>
          <TabsTrigger value="settings">Paramètres</TabsTrigger>
          <TabsTrigger value="preview">Aperçu</TabsTrigger>
        </TabsList>

        <TabsContent value="content" className="space-y-4 mt-4">
          {/* Templates */}
          {templates && templates.length > 0 && (
            <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-lg">
              <Sparkles className="h-5 w-5 text-purple-600" />
              <Select value={selectedTemplateId} onValueChange={setSelectedTemplateId}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Utiliser un template..." />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={handleApplyTemplate}
                disabled={!selectedTemplateId}
              >
                Appliquer
              </Button>
            </div>
          )}

          {/* Titre (optionnel) */}
          <div className="space-y-2">
            <Label htmlFor="title">Titre (interne)</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Promo rentrée 2026"
            />
          </div>

          {/* Contenu */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="content">Contenu *</Label>
              <span className={`text-sm ${characterCount > getCharLimit() ? 'text-red-500' : 'text-gray-500'}`}>
                {characterCount} / {getCharLimit()}
              </span>
            </div>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Votre message..."
              rows={6}
              className="resize-none"
            />
          </div>

          {/* Lien CTA */}
          <div className="space-y-2">
            <Label htmlFor="link">
              <LinkIcon className="h-4 w-4 inline mr-1" />
              Lien (call-to-action)
            </Label>
            <Input
              id="link"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              placeholder="https://azalscore.com/demo"
            />
            <p className="text-xs text-gray-500">
              Les paramètres UTM seront ajoutés automatiquement pour le tracking.
            </p>
          </div>

          {/* Hashtags */}
          <div className="space-y-2">
            <Label htmlFor="hashtags">
              <Hash className="h-4 w-4 inline mr-1" />
              Hashtags
            </Label>
            <Input
              id="hashtags"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              placeholder="#ERP #SaaS #GestionEntreprise"
            />
          </div>

          {/* Plateformes */}
          <div className="space-y-2">
            <Label>Plateformes *</Label>
            <div className="flex flex-wrap gap-3">
              {PLATFORM_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Checkbox
                    checked={platforms.includes(opt.value as MarketingPlatform)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setPlatforms([...platforms, opt.value as MarketingPlatform]);
                      } else {
                        setPlatforms(platforms.filter((p) => p !== opt.value));
                      }
                    }}
                  />
                  <span>{opt.label}</span>
                </label>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4 mt-4">
          {/* Campagne */}
          {campaigns && campaigns.length > 0 && (
            <div className="space-y-2">
              <Label>Campagne</Label>
              <Select value={campaignId} onValueChange={setCampaignId}>
                <SelectTrigger>
                  <SelectValue placeholder="Aucune campagne" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Aucune campagne</SelectItem>
                  {campaigns.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Type de post */}
          <div className="space-y-2">
            <Label>Type de publication</Label>
            <Select value={postType} onValueChange={(v) => setPostType(v as PostType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {POST_TYPE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Programmation */}
          <div className="space-y-2">
            <Label>Programmer la publication</Label>
            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="flex-1 justify-start">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    {scheduledDate
                      ? format(scheduledDate, 'PPP', { locale: fr })
                      : 'Choisir une date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={scheduledDate}
                    onSelect={setScheduledDate}
                    disabled={(date) => date < new Date()}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              <Input
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="w-[120px]"
              />
            </div>

            {optimalTime && (
              <Button
                variant="link"
                size="sm"
                onClick={handleApplyOptimalTime}
                className="text-purple-600"
              >
                <Sparkles className="h-3 w-3 mr-1" />
                Meilleur moment suggéré: {optimalTime.day} {optimalTime.time}
              </Button>
            )}
          </div>
        </TabsContent>

        <TabsContent value="preview" className="mt-4">
          <div className="border rounded-lg p-4 bg-gray-50">
            <div className="max-w-md mx-auto bg-white rounded-lg shadow p-4 space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                  AZ
                </div>
                <div>
                  <div className="font-semibold">AZALSCORE</div>
                  <div className="text-xs text-gray-500">Maintenant</div>
                </div>
              </div>
              <p className="whitespace-pre-wrap">{content || 'Votre message apparaîtra ici...'}</p>
              {linkUrl && (
                <div className="border rounded p-2 bg-gray-50">
                  <div className="text-sm text-blue-600 truncate">{linkUrl}</div>
                </div>
              )}
              {hashtags && (
                <p className="text-blue-600 text-sm">{hashtags}</p>
              )}
              <div className="flex items-center gap-4 text-gray-500 text-sm pt-2 border-t">
                <span>0 J'aime</span>
                <span>0 Commentaires</span>
                <span>0 Partages</span>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={onClose}>
          Annuler
        </Button>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleSaveDraft}
            disabled={!isValid || createPost.isPending || updatePost.isPending}
          >
            <Save className="h-4 w-4 mr-2" />
            Brouillon
          </Button>
          {scheduledDate && (
            <Button
              variant="secondary"
              onClick={handleSchedule}
              disabled={!isValid || createPost.isPending || schedulePost.isPending}
            >
              <Clock className="h-4 w-4 mr-2" />
              Programmer
            </Button>
          )}
          <Button
            onClick={handlePublishNow}
            disabled={!isValid || createPost.isPending || publishPost.isPending}
          >
            <Send className="h-4 w-4 mr-2" />
            Publier maintenant
          </Button>
        </div>
      </div>
    </div>
  );
}
