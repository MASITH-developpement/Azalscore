// @ts-nocheck
/**
 * AZALSCORE Module - Training
 * Interface principale du module de formation
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Card, PageWrapper, Grid } from '@ui/layout';
import { Input, Select } from '@ui/forms';
import { DataTable } from '@ui/tables';
import { LoadingState, EmptyState } from '@ui/components/StateViews';
import type { TableColumn } from '@/types';
import {
  GraduationCap,
  BookOpen,
  Calendar,
  UserCheck,
  User,
  Award,
  Plus,
  Search,
  Users,
  Clock,
  MapPin,
  Video,
  Play,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import {
  useTrainingDashboard,
  useCourseList,
  useSessionList,
  useMyEnrollments,
  useMyCertificates,
  useTrainerList,
  useEnroll,
  useCancelEnrollment,
} from './hooks';
import type {
  TrainingCourse,
  TrainingSession,
  Enrollment,
  Trainer,
  Certificate,
  TrainingType,
  TrainingLevel,
  SessionStatus,
  EnrollmentStatus,
  CertificateStatus,
} from './types';
import {
  TRAINING_TYPE_CONFIG,
  TRAINING_LEVEL_CONFIG,
  SESSION_STATUS_CONFIG,
  ENROLLMENT_STATUS_CONFIG,
  CERTIFICATE_STATUS_CONFIG,
} from './types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ variant?: string; className?: string; children: React.ReactNode }> = ({ variant = 'default', className = '', children }) => (
  <span className={`azals-badge azals-badge--${variant} ${className}`}>{children}</span>
);

const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

const Progress: React.FC<{ value: number; className?: string }> = ({ value, className = '' }) => (
  <div className={`h-2 bg-gray-200 rounded-full overflow-hidden ${className}`}>
    <div
      className="h-full bg-primary transition-all"
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);

// Simple Tabs components
const Tabs: React.FC<{ defaultValue: string; children: React.ReactNode }> = ({ defaultValue, children }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);
  return (
    <div className="azals-tabs">
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (v: string) => void }>, { activeTab, setActiveTab });
        }
        return child;
      })}
    </div>
  );
};

const TabsList: React.FC<{ children: React.ReactNode; activeTab?: string; setActiveTab?: (v: string) => void }> = ({ children, activeTab, setActiveTab }) => (
  <div className="azals-tabs__list flex gap-2 border-b mb-4" role="tablist">
    {React.Children.map(children, (child) => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (v: string) => void }>, { activeTab, setActiveTab });
      }
      return child;
    })}
  </div>
);

const TabsTrigger: React.FC<{ value: string; children: React.ReactNode; activeTab?: string; setActiveTab?: (v: string) => void }> = ({ value, children, activeTab, setActiveTab }) => (
  <button
    type="button"
    role="tab"
    className={`px-4 py-2 border-b-2 transition-colors ${activeTab === value ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
    aria-selected={activeTab === value}
    onClick={() => setActiveTab?.(value)}
  >
    <span className="flex items-center gap-2">{children}</span>
  </button>
);

const TabsContent: React.FC<{ value: string; children: React.ReactNode; className?: string; activeTab?: string }> = ({ value, children, className = '', activeTab }) => {
  if (activeTab !== value) return null;
  return <div className={className} role="tabpanel">{children}</div>;
};

// ============================================================================
// HELPERS
// ============================================================================

function toNum(value: number | string | undefined): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'number') return value;
  return parseFloat(value) || 0;
}

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

function formatDuration(hours: number | string | undefined): string {
  const h = toNum(hours);
  if (h === 0) return '-';
  if (h < 1) return `${Math.round(h * 60)} min`;
  return `${h}h`;
}

// ============================================================================
// STATUS BADGES
// ============================================================================

interface SessionStatusBadgeProps {
  status: SessionStatus;
}

function SessionStatusBadge({ status }: SessionStatusBadgeProps) {
  const config = SESSION_STATUS_CONFIG[status];
  const colorMap: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

interface EnrollmentStatusBadgeProps {
  status: EnrollmentStatus;
}

function EnrollmentStatusBadge({ status }: EnrollmentStatusBadgeProps) {
  const config = ENROLLMENT_STATUS_CONFIG[status];
  const colorMap: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// STATS CARDS
// ============================================================================

interface StatsCardsProps {
  stats: {
    total_courses: number;
    upcoming_sessions: number;
    total_participants: number;
    certificates_issued: number;
  };
}

function StatsCards({ stats }: StatsCardsProps) {
  return (
    <Grid cols={4} gap="md">
      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <BookOpen className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Formations</p>
            <p className="text-2xl font-bold">{stats.total_courses}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Calendar className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Sessions a venir</p>
            <p className="text-2xl font-bold">{stats.upcoming_sessions}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Users className="h-5 w-5 text-orange-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Participants</p>
            <p className="text-2xl font-bold">{stats.total_participants}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Award className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Certificats</p>
            <p className="text-2xl font-bold">{stats.certificates_issued}</p>
          </div>
        </div>
      </Card>
    </Grid>
  );
}

// ============================================================================
// COURSES TAB (Catalogue)
// ============================================================================

function CoursesTab() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading } = useCourseList({
    search: search || undefined,
    training_type: (typeFilter || undefined) as TrainingType | undefined,
  });

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            
            placeholder="Rechercher une formation..."
            value={search}
            onChange={(value) => setSearch(String(value))}
          />
        </div>
        <Select
          
          value={typeFilter}
          onChange={(value) => setTypeFilter(String(value))}
          options={[
            { value: '', label: 'Tous les types' },
            ...Object.entries(TRAINING_TYPE_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouvelle formation
        </Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <Grid cols={3} gap="md">
          {data.items.map((course) => (
            <Card key={course.id} className="cursor-pointer hover:shadow-md transition-shadow">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium">{course.name}</h3>
                    {course.description && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {course.description}
                      </p>
                    )}
                  </div>
                  {course.training_type === 'elearning' && (
                    <Video className="h-5 w-5 text-blue-500" />
                  )}
                </div>

                <div className="flex flex-wrap gap-2 mt-3">
                  <Badge variant="secondary">
                    {TRAINING_TYPE_CONFIG[course.training_type]?.label || course.training_type}
                  </Badge>
                  <Badge variant="secondary">
                    {TRAINING_LEVEL_CONFIG[course.level]?.label || course.level}
                  </Badge>
                </div>

                <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDuration(course.duration_hours)}
                  </span>
                  {course.price !== undefined && (
                    <span className="font-medium text-foreground">
                      {toNum(course.price).toFixed(0)} EUR
                    </span>
                  )}
                </div>

                <Button className="w-full mt-4" variant="secondary">
                  Voir les sessions
                </Button>
              </div>
            </Card>
          ))}
        </Grid>
      ) : (
        <EmptyState
          icon={<BookOpen className="h-12 w-12" />}
          title="Aucune formation"
          message="Creez votre premiere formation pour commencer."
          action={{
            label: 'Creer une formation',
            onClick: () => {},
            icon: <Plus className="h-4 w-4" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// SESSIONS TAB
// ============================================================================

function SessionsTab() {
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useSessionList({
    status: (statusFilter || undefined) as SessionStatus | undefined,
  });

  const enroll = useEnroll();

  const columns: TableColumn<TrainingSession>[] = [
    {
      id: 'course_name',
      header: 'Formation',
      accessor: 'course_name',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.course_name}</p>
          <p className="text-sm text-muted-foreground">Session: {row.code}</p>
        </div>
      ),
    },
    {
      id: 'start_date',
      header: 'Dates',
      accessor: 'start_date',
      render: (_, row) => (
        <div>
          <p>{formatDate(row.start_date)}</p>
          {row.end_date && row.end_date !== row.start_date && (
            <p className="text-sm text-muted-foreground">au {formatDate(row.end_date)}</p>
          )}
        </div>
      ),
    },
    {
      id: 'location',
      header: 'Lieu',
      accessor: 'location',
      render: (_, row) => (
        <div className="flex items-center gap-1">
          {row.is_virtual ? <Video className="h-4 w-4" /> : <MapPin className="h-4 w-4" />}
          <span>{row.is_virtual ? 'En ligne' : row.location || '-'}</span>
        </div>
      ),
    },
    {
      id: 'trainer_name',
      header: 'Formateur',
      accessor: 'trainer_name',
    },
    {
      id: 'enrolled_count',
      header: 'Places',
      accessor: 'enrolled_count',
      render: (_, row) => (
        <span>
          {row.enrolled_count || 0}/{row.max_participants}
        </span>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <SessionStatusBadge status={row.status} />,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-2">
          {row.status === 'open' && (row.enrolled_count || 0) < row.max_participants && (
            <Button
              size="sm"
              onClick={() => enroll.mutate({ session_id: row.id })}
            >
              S'inscrire
            </Button>
          )}
          <Button size="sm" variant="secondary">
            Details
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Select
          
          value={statusFilter}
          onChange={(value) => setStatusFilter(String(value))}
          options={[
            { value: '', label: 'Tous les statuts' },
            ...Object.entries(SESSION_STATUS_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
        <Button className="ml-auto" leftIcon={<Plus className="h-4 w-4" />}>
          Nouvelle session
        </Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <DataTable
          data={data.items}
          columns={columns}
          keyField="id"
        />
      ) : (
        <EmptyState
          icon={<Calendar className="h-12 w-12" />}
          title="Aucune session"
          message="Planifiez votre premiere session de formation."
          action={{
            label: 'Planifier une session',
            onClick: () => {},
            icon: <Plus className="h-4 w-4" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// TRAINERS TAB
// ============================================================================

function TrainersTab() {
  const { data: trainers, isLoading } = useTrainerList();

  const columns: TableColumn<Trainer>[] = [
    {
      id: 'name',
      header: 'Formateur',
      accessor: 'name',
      render: (_, row) => (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
            <UserCheck className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="font-medium">{row.name}</p>
            <p className="text-sm text-muted-foreground">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      id: 'specialization',
      header: 'Specialisation',
      accessor: 'specialization',
    },
    {
      id: 'is_internal',
      header: 'Type',
      accessor: 'is_internal',
      render: (_, row) => (
        <Badge variant={row.is_internal ? 'default' : 'secondary'}>
          {row.is_internal ? 'Interne' : 'Externe'}
        </Badge>
      ),
    },
    {
      id: 'daily_rate',
      header: 'Tarif journalier',
      accessor: 'daily_rate',
      render: (_, row) => row.daily_rate ? `${toNum(row.daily_rate).toFixed(0)} EUR` : '-',
    },
    {
      id: 'average_rating',
      header: 'Note moyenne',
      accessor: 'average_rating',
      render: (_, row) => row.average_rating ? `${toNum(row.average_rating).toFixed(1)}/5` : '-',
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (_, row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!trainers || trainers.length === 0) {
    return (
      <EmptyState
        icon={<UserCheck className="h-12 w-12" />}
        title="Aucun formateur"
        message="Ajoutez vos formateurs pour pouvoir planifier des sessions."
        action={{
          label: 'Ajouter un formateur',
          onClick: () => {},
          icon: <Plus className="h-4 w-4" />,
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Ajouter un formateur
        </Button>
      </div>
      <DataTable
        data={trainers}
        columns={columns}
        keyField="id"
      />
    </div>
  );
}

// ============================================================================
// MY TRAININGS TAB
// ============================================================================

function MyTrainingsTab() {
  const { data: enrollments, isLoading } = useMyEnrollments();
  const cancelEnrollment = useCancelEnrollment();

  const columns: TableColumn<Enrollment>[] = [
    {
      id: 'course_name',
      header: 'Formation',
      accessor: 'course_name',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.course_name}</p>
          <p className="text-sm text-muted-foreground">Session: {row.session_code}</p>
        </div>
      ),
    },
    {
      id: 'session_start_date',
      header: 'Date',
      accessor: 'session_start_date',
      render: (_, row) => formatDate(row.session_start_date),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <EnrollmentStatusBadge status={row.status} />,
    },
    {
      id: 'progress_percent',
      header: 'Progression',
      accessor: 'progress_percent',
      render: (_, row) => (
        <div className="w-32">
          <Progress value={row.progress_percent || 0} />
          <p className="text-xs text-muted-foreground mt-1">{row.progress_percent || 0}%</p>
        </div>
      ),
    },
    {
      id: 'attendance_rate',
      header: 'Presence',
      accessor: 'attendance_rate',
      render: (_, row) => `${row.attendance_rate || 0}%`,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-2">
          {row.status === 'enrolled' && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => cancelEnrollment.mutate(row.id)}
            >
              Annuler
            </Button>
          )}
          {row.status === 'in_progress' && (
            <Button size="sm" leftIcon={<Play className="h-4 w-4" />}>
              Continuer
            </Button>
          )}
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!enrollments || enrollments.length === 0) {
    return (
      <EmptyState
        icon={<User className="h-12 w-12" />}
        title="Aucune inscription"
        message="Vous n'etes inscrit a aucune formation pour le moment."
        action={{
          label: 'Voir le catalogue',
          onClick: () => {},
          icon: <BookOpen className="h-4 w-4" />,
        }}
      />
    );
  }

  return (
    <DataTable
      data={enrollments}
      columns={columns}
      keyField="id"
    />
  );
}

// ============================================================================
// CERTIFICATES TAB
// ============================================================================

function CertificatesTab() {
  const { data: certificates, isLoading } = useMyCertificates();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!certificates || certificates.length === 0) {
    return (
      <EmptyState
        icon={<Award className="h-12 w-12" />}
        title="Aucun certificat"
        message="Completez des formations pour obtenir vos certificats."
      />
    );
  }

  return (
    <Grid cols={3} gap="md">
      {certificates.map((cert) => (
        <Card key={cert.id} className="border-2 border-dashed">
          <div className="p-6 text-center">
            <Award className="h-12 w-12 mx-auto text-yellow-500 mb-4" />
            <h3 className="font-bold text-lg">{cert.course_name}</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Delivre le {formatDate(cert.issued_at)}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              N {cert.certificate_number}
            </p>
            {cert.score !== undefined && (
              <Badge className="mt-3">
                Score: {cert.score}%
              </Badge>
            )}
            <div className="flex gap-2 mt-4 justify-center">
              <Button size="sm" variant="secondary">
                Telecharger
              </Button>
              <Button size="sm" variant="secondary">
                Verifier
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </Grid>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function TrainingModule() {
  const { data: dashboard, isLoading } = useTrainingDashboard();

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Grid cols={4} gap="md">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </Grid>
        <Skeleton className="h-96" />
      </div>
    );
  }

  const stats = dashboard?.stats || {
    total_courses: 0,
    upcoming_sessions: 0,
    total_participants: 0,
    certificates_issued: 0,
  };

  return (
    <PageWrapper
      title="Formation"
      subtitle="Gestion des formations, sessions et certifications"
      actions={
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouvelle formation
        </Button>
      }
    >
      <div className="space-y-6">
        <StatsCards stats={stats} />

        <Tabs defaultValue="my">
          <TabsList>
            <TabsTrigger value="my">
              <User className="h-4 w-4 mr-2" />
              Mes formations
            </TabsTrigger>
            <TabsTrigger value="catalog">
              <BookOpen className="h-4 w-4 mr-2" />
              Catalogue
            </TabsTrigger>
            <TabsTrigger value="sessions">
              <Calendar className="h-4 w-4 mr-2" />
              Sessions
            </TabsTrigger>
            <TabsTrigger value="trainers">
              <UserCheck className="h-4 w-4 mr-2" />
              Formateurs
            </TabsTrigger>
            <TabsTrigger value="certificates">
              <Award className="h-4 w-4 mr-2" />
              Certificats
            </TabsTrigger>
          </TabsList>

          <TabsContent value="my" className="mt-6">
            <MyTrainingsTab />
          </TabsContent>

          <TabsContent value="catalog" className="mt-6">
            <CoursesTab />
          </TabsContent>

          <TabsContent value="sessions" className="mt-6">
            <SessionsTab />
          </TabsContent>

          <TabsContent value="trainers" className="mt-6">
            <TrainersTab />
          </TabsContent>

          <TabsContent value="certificates" className="mt-6">
            <CertificatesTab />
          </TabsContent>
        </Tabs>
      </div>
    </PageWrapper>
  );
}

// Named exports
export { TrainingModule };
export * from './types';
export * from './hooks';
export * from './api';
export { trainingMeta } from './meta';
