/**
 * AZALSCORE - Liste des Publications
 * ===================================
 * Design moderne avec icônes sociales et interface engageante
 */

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
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
} from '@/components/ui/dialog';
import {
  Plus,
  MoreVertical,
  Send,
  Clock,
  Edit2,
  Copy,
  Trash2,
  Eye,
  Calendar,
  Search,
  Filter,
  Heart,
  MessageCircle,
  Share2,
  MousePointerClick,
  Image,
  Video,
  Link as LinkIcon,
  FileText,
  Layers,
  Sparkles,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

import { usePosts, useDeletePost, usePublishPost, useDuplicatePost } from '../api';
import { PostEditor } from './PostEditor';
import type { SocialPost, PostStatus, MarketingPlatform, PostType } from '../types';
import { POST_STATUS_OPTIONS } from '../types';

// Icônes SVG des plateformes
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

const platformColors: Record<string, string> = {
  meta_facebook: 'text-blue-600 bg-blue-50 border-blue-200',
  meta_instagram: 'text-pink-600 bg-pink-50 border-pink-200',
  linkedin: 'text-sky-700 bg-sky-50 border-sky-200',
  twitter: 'text-slate-800 bg-slate-100 border-slate-200',
  tiktok: 'text-slate-900 bg-slate-50 border-slate-200',
  youtube: 'text-red-600 bg-red-50 border-red-200',
};

const statusConfig: Record<PostStatus, { icon: React.ReactNode; color: string; bg: string }> = {
  draft: {
    icon: <FileText className="h-3.5 w-3.5" />,
    color: 'text-gray-600',
    bg: 'bg-gray-100'
  },
  scheduled: {
    icon: <Clock className="h-3.5 w-3.5" />,
    color: 'text-blue-600',
    bg: 'bg-blue-100'
  },
  publishing: {
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
    color: 'text-amber-600',
    bg: 'bg-amber-100'
  },
  published: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    color: 'text-emerald-600',
    bg: 'bg-emerald-100'
  },
  failed: {
    icon: <XCircle className="h-3.5 w-3.5" />,
    color: 'text-red-600',
    bg: 'bg-red-100'
  },
  archived: {
    icon: <FileText className="h-3.5 w-3.5" />,
    color: 'text-gray-400',
    bg: 'bg-gray-50'
  },
};

const postTypeIcons: Record<PostType, React.ReactNode> = {
  text: <FileText className="h-4 w-4" />,
  image: <Image className="h-4 w-4" />,
  video: <Video className="h-4 w-4" />,
  carousel: <Layers className="h-4 w-4" />,
  link: <LinkIcon className="h-4 w-4" />,
  story: <Clock className="h-4 w-4" />,
  reel: <Video className="h-4 w-4" />,
};

export function PostsList() {
  const [statusFilter, setStatusFilter] = useState<PostStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [selectedPost, setSelectedPost] = useState<SocialPost | null>(null);

  const { data: posts, isLoading } = usePosts({
    status: statusFilter === 'all' ? undefined : statusFilter,
    limit: 50,
  });

  const deletePost = useDeletePost();
  const publishPost = usePublishPost();
  const duplicatePost = useDuplicatePost();

  const filteredPosts = posts?.filter((post) =>
    post.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    post.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEdit = (post: SocialPost) => {
    setSelectedPost(post);
    setIsEditorOpen(true);
  };

  const handleNew = () => {
    setSelectedPost(null);
    setIsEditorOpen(true);
  };

  const handlePublish = async (post: SocialPost) => {
    if (confirm('Publier cette publication maintenant ?')) {
      await publishPost.mutateAsync({ id: post.id });
    }
  };

  const handleDuplicate = async (post: SocialPost) => {
    await duplicatePost.mutateAsync(post.id);
  };

  const handleDelete = async (post: SocialPost) => {
    if (confirm('Supprimer cette publication ?')) {
      await deletePost.mutateAsync(post.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toolbar moderne */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 w-full sm:w-auto">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher une publication..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white border-gray-200 focus:border-indigo-300 focus:ring-indigo-200"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as PostStatus | 'all')}
          >
            <SelectTrigger className="w-[160px] bg-white">
              <Filter className="h-4 w-4 mr-2 text-gray-400" />
              <SelectValue placeholder="Statut" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              {POST_STATUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  <span className="flex items-center gap-2">
                    {statusConfig[opt.value as PostStatus]?.icon}
                    {opt.label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          onClick={handleNew}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md"
        >
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle publication
        </Button>
      </div>

      {/* Grille de publications */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <Loader2 className="h-10 w-10 animate-spin text-indigo-500 mx-auto mb-4" />
            <p className="text-gray-500">Chargement des publications...</p>
          </div>
        </div>
      ) : filteredPosts?.length === 0 ? (
        <Card className="border-dashed border-2 border-gray-200 bg-gradient-to-br from-gray-50 to-white">
          <CardContent className="py-16">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
                <Sparkles className="h-10 w-10 text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Aucune publication trouvée
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Créez votre première publication pour commencer à engager votre audience sur les réseaux sociaux.
              </p>
              <Button
                onClick={handleNew}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Créer ma première publication
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPosts?.map((post) => {
            const status = statusConfig[post.status];

            return (
              <Card
                key={post.id}
                className="group border-0 shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden"
              >
                {/* Prévisualisation média */}
                {post.media_urls.length > 0 && (
                  <div className="relative h-40 bg-gradient-to-br from-gray-100 to-gray-50 overflow-hidden">
                    <img
                      src={post.media_urls[0]}
                      alt=""
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    {post.media_urls.length > 1 && (
                      <span className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded-full">
                        +{post.media_urls.length - 1}
                      </span>
                    )}
                    <div className="absolute top-2 left-2">
                      <span className="bg-white/90 backdrop-blur-sm p-1.5 rounded-lg shadow-sm">
                        {postTypeIcons[post.post_type]}
                      </span>
                    </div>
                  </div>
                )}

                <CardContent className="p-4">
                  {/* Header avec statut */}
                  <div className="flex items-start justify-between mb-3">
                    <Badge className={`${status.bg} ${status.color} border-0 font-medium`}>
                      <span className="flex items-center gap-1.5">
                        {status.icon}
                        {POST_STATUS_OPTIONS.find(o => o.value === post.status)?.label}
                      </span>
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEdit(post)}>
                          <Edit2 className="h-4 w-4 mr-2" />
                          Modifier
                        </DropdownMenuItem>
                        {post.status === 'draft' && (
                          <DropdownMenuItem onClick={() => handlePublish(post)}>
                            <Send className="h-4 w-4 mr-2" />
                            Publier maintenant
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem onClick={() => handleDuplicate(post)}>
                          <Copy className="h-4 w-4 mr-2" />
                          Dupliquer
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(post)}
                          className="text-red-600 focus:text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Supprimer
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  {/* Contenu */}
                  <div className="mb-3">
                    {post.title && (
                      <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">
                        {post.title}
                      </h3>
                    )}
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {post.content}
                    </p>
                  </div>

                  {/* Hashtags */}
                  {post.hashtags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {post.hashtags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                      {post.hashtags.length > 3 && (
                        <span className="text-xs text-gray-400">
                          +{post.hashtags.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Plateformes */}
                  <div className="flex items-center gap-1.5 mb-3">
                    {post.platforms.map((platform) => {
                      const Icon = PlatformIcons[platform];
                      const colors = platformColors[platform] || 'text-gray-600 bg-gray-50';
                      return (
                        <span
                          key={platform}
                          className={`w-7 h-7 rounded-lg flex items-center justify-center border ${colors}`}
                          title={platform.replace('meta_', '').replace('_', ' ')}
                        >
                          {Icon ? <Icon className="w-3.5 h-3.5" /> : '?'}
                        </span>
                      );
                    })}
                  </div>

                  {/* Date */}
                  <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
                    {post.scheduled_at ? (
                      <span className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-blue-500" />
                        {format(new Date(post.scheduled_at), 'dd MMM à HH:mm', { locale: fr })}
                      </span>
                    ) : post.published_at ? (
                      <span className="flex items-center gap-1.5 text-emerald-600">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {format(new Date(post.published_at), 'dd MMM à HH:mm', { locale: fr })}
                      </span>
                    ) : (
                      <span className="text-gray-400">Non programmé</span>
                    )}

                    {/* Stats si publié */}
                    {post.status === 'published' && (
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1" title="Vues">
                          <Eye className="h-3.5 w-3.5" />
                          {post.impressions > 1000
                            ? `${(post.impressions / 1000).toFixed(1)}k`
                            : post.impressions}
                        </span>
                        <span className="flex items-center gap-1" title="Likes">
                          <Heart className="h-3.5 w-3.5 text-red-400" />
                          {post.likes}
                        </span>
                        <span className="flex items-center gap-1" title="Clics">
                          <MousePointerClick className="h-3.5 w-3.5 text-blue-400" />
                          {post.clicks}
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Dialog éditeur */}
      <Dialog open={isEditorOpen} onOpenChange={setIsEditorOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedPost ? (
                <>
                  <Edit2 className="h-5 w-5 text-indigo-500" />
                  Modifier la publication
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5 text-indigo-500" />
                  Nouvelle publication
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          <PostEditor
            post={selectedPost}
            onClose={() => {
              setIsEditorOpen(false);
              setSelectedPost(null);
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
