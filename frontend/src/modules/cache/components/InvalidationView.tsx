/**
 * AZALSCORE Module - Cache - Invalidation View
 * Interface d'invalidation de cache
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { Card } from '@ui/layout';
import { cacheApi } from '../api';
import { cacheKeys } from '../hooks';
import { useQueryClient, useMutation } from '@tanstack/react-query';

export const InvalidationView: React.FC = () => {
  const [invalidationType, setInvalidationType] = useState<'key' | 'pattern' | 'tag' | 'entity'>('key');
  const [inputValue, setInputValue] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const queryClient = useQueryClient();

  const invalidateMutation = useMutation({
    mutationFn: async () => {
      switch (invalidationType) {
        case 'key':
          return cacheApi.invalidateByKey(inputValue);
        case 'pattern':
          return cacheApi.invalidateByPattern(inputValue);
        case 'tag':
          return cacheApi.invalidateByTag(inputValue);
        case 'entity':
          return cacheApi.invalidateByEntity(entityType, entityId || undefined);
        default:
          throw new Error('Type invalide');
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
      alert(`Invalidation reussie: ${result.data.keys_invalidated} cles invalidees`);
      setInputValue('');
      setEntityType('');
      setEntityId('');
    },
    onError: (error) => {
      alert(`Erreur: ${error}`);
    },
  });

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Invalidation de cache</h3>

      <div className="space-y-4">
        <div className="flex gap-4">
          <Select
            value={invalidationType}
            onChange={(v) => setInvalidationType(v as typeof invalidationType)}
            options={[
              { value: 'key', label: 'Par cle' },
              { value: 'pattern', label: 'Par pattern' },
              { value: 'tag', label: 'Par tag' },
              { value: 'entity', label: 'Par entite' },
            ]}
            className="w-40"
          />
        </div>

        {invalidationType === 'entity' ? (
          <div className="flex gap-4">
            <Input
              value={entityType}
              onChange={setEntityType}
              placeholder="Type d'entite (ex: User)"
              className="flex-1"
            />
            <Input
              value={entityId}
              onChange={setEntityId}
              placeholder="ID entite (optionnel)"
              className="flex-1"
            />
          </div>
        ) : (
          <Input
            value={inputValue}
            onChange={setInputValue}
            placeholder={
              invalidationType === 'key'
                ? 'Cle a invalider (ex: user:123)'
                : invalidationType === 'pattern'
                ? 'Pattern (ex: user:*)'
                : 'Tag (ex: users)'
            }
            className="w-full"
          />
        )}

        <Button
          onClick={() => invalidateMutation.mutate()}
          disabled={
            invalidateMutation.isPending ||
            (invalidationType === 'entity' ? !entityType : !inputValue)
          }
        >
          {invalidateMutation.isPending ? 'Invalidation...' : 'Invalider'}
        </Button>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded">
        <h4 className="font-semibold mb-2">Aide</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li><strong>Par cle:</strong> Invalide une cle specifique</li>
          <li><strong>Par pattern:</strong> Utilise * comme wildcard (ex: user:* invalide user:1, user:2, etc.)</li>
          <li><strong>Par tag:</strong> Invalide toutes les cles avec ce tag</li>
          <li><strong>Par entite:</strong> Invalide les cles liees a une entite metier</li>
        </ul>
      </div>
    </Card>
  );
};

export default InvalidationView;
