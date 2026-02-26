/**
 * AZALSCORE Module - Admin - UsersPermissionsView
 * Vue de liste des utilisateurs avec gestion des permissions
 */

import React, { useState } from 'react';
import { Key } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { useUsers } from '../hooks';
import UserPermissionsModal from './UserPermissionsModal';

interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role_name?: string;
}

const UsersPermissionsView: React.FC = () => {
  const { data: users = [], isLoading } = useUsers({});
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);

  const handleOpenPermissions = (user: User) => {
    setSelectedUser(user);
    setShowPermissionsModal(true);
  };

  const columns: TableColumn<User>[] = [
    { id: 'username', header: 'Utilisateur', accessor: 'username' },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'last_name', header: 'Nom', accessor: 'last_name', render: (_, row) =>
      `${(row as User).first_name || ''} ${(row as User).last_name || ''}`.trim() || '-'
    },
    { id: 'role_name', header: 'Role', accessor: 'role_name', render: (v) => (v as string) || '-' },
    { id: 'actions', header: 'Permissions', accessor: 'id', render: (_, row) => {
      const user = row as User;
      return (
        <div onClick={(e) => e.stopPropagation()}>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleOpenPermissions(user)}
          >
            <Key size={14} className="mr-1" />
            Gerer
          </Button>
        </div>
      );
    }}
  ];

  return (
    <Card>
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Gestion des Permissions par Utilisateur</h3>
        <p className="text-sm text-gray-500 mt-1">
          Configurez les acces specifiques a chaque module et fonctionnalite pour chaque utilisateur.
        </p>
      </div>
      <DataTable columns={columns} data={users} isLoading={isLoading} keyField="id" filterable />

      <UserPermissionsModal
        isOpen={showPermissionsModal}
        user={selectedUser}
        onClose={() => {
          setShowPermissionsModal(false);
          setSelectedUser(null);
        }}
      />
    </Card>
  );
};

export default UsersPermissionsView;
