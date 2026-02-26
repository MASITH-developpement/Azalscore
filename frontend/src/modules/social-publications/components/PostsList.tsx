/**
 * AZALSCORE - Liste des Publications
 * ===================================
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
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Plus,
  MoreHorizontal,
  Send,
  Clock,
  Edit,
  Copy,
  Trash2,
  Eye,
  Calendar,
  Search,
  Filter,
} from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

import { usePosts, useDeletePost, usePublishPost, useDuplicatePost } from '../api';
import { PostEditor } from './PostEditor';
import type { SocialPost, PostStatus, MarketingPlatform } from '../types';
import { POST_STATUS_OPTIONS, PLATFORM_OPTIONS } from '../types';

const getStatusColor = (status: PostStatus) => {
  const colors: Record<PostStatus, string> = {
    draft: 'bg-gray-100 text-gray-800',
    scheduled: 'bg-blue-100 text-blue-800',
    publishing: 'bg-yellow-100 text-yellow-800',
    published: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    archived: 'bg-gray-100 text-gray-600',
  };
  return colors[status] || 'bg-gray-100';
};

const getPlatformIcon = (platform: MarketingPlatform) => {
  const icons: Partial<Record<MarketingPlatform, string>> = {
    meta_facebook: 'F',
    meta_instagram: 'I',
    linkedin: 'in',
    twitter: 'X',
    tiktok: 'T',
    youtube: 'Y',
  };
  return icons[platform] || '?';
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
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as PostStatus | 'all')}
          >
            <SelectTrigger className="w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Statut" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              {POST_STATUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Dialog open={isEditorOpen} onOpenChange={setIsEditorOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleNew}>
              <Plus className="h-4 w-4 mr-2" />
              Nouvelle publication
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {selectedPost ? 'Modifier la publication' : 'Nouvelle publication'}
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

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Chargement...</div>
      ) : filteredPosts?.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          Aucune publication trouvée.
          <br />
          <Button variant="link" onClick={handleNew}>
            Créer votre première publication
          </Button>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Contenu</TableHead>
              <TableHead>Plateformes</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Performance</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredPosts?.map((post) => (
              <TableRow key={post.id}>
                <TableCell>
                  <div className="space-y-1">
                    {post.title && (
                      <div className="font-medium">{post.title}</div>
                    )}
                    <div className="text-sm text-gray-600 line-clamp-2">
                      {post.content}
                    </div>
                    {post.hashtags.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {post.hashtags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="text-xs text-blue-600 bg-blue-50 px-1 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                        {post.hashtags.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{post.hashtags.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    {post.platforms.map((p) => (
                      <span
                        key={p}
                        className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-xs font-medium"
                        title={PLATFORM_OPTIONS.find((o) => o.value === p)?.label}
                      >
                        {getPlatformIcon(p)}
                      </span>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className={getStatusColor(post.status)}>
                    {POST_STATUS_OPTIONS.find((o) => o.value === post.status)?.label}
                  </Badge>
                </TableCell>
                <TableCell>
                  {post.scheduled_at ? (
                    <div className="flex items-center gap-1 text-sm">
                      <Clock className="h-3 w-3" />
                      {format(new Date(post.scheduled_at), 'dd/MM HH:mm', {
                        locale: fr,
                      })}
                    </div>
                  ) : post.published_at ? (
                    <div className="flex items-center gap-1 text-sm text-green-600">
                      <Send className="h-3 w-3" />
                      {format(new Date(post.published_at), 'dd/MM HH:mm', {
                        locale: fr,
                      })}
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">-</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {post.status === 'published' ? (
                    <div className="text-sm space-y-1">
                      <div>{post.impressions.toLocaleString()} vues</div>
                      <div className="text-gray-500">
                        {post.clicks} clics &middot; {post.likes} likes
                      </div>
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEdit(post)}>
                        <Edit className="h-4 w-4 mr-2" />
                        Modifier
                      </DropdownMenuItem>
                      {post.status === 'draft' && (
                        <DropdownMenuItem onClick={() => handlePublish(post)}>
                          <Send className="h-4 w-4 mr-2" />
                          Publier
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem onClick={() => handleDuplicate(post)}>
                        <Copy className="h-4 w-4 mr-2" />
                        Dupliquer
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDelete(post)}
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
