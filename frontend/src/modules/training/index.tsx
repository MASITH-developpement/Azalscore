/**
 * AZALSCORE Module - Training
 * Interface principale du module de formation
 */

import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  DataTable,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Input,
  Select,
  Skeleton,
  EmptyState,
  Progress,
} from '@/ui-engine';
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

function formatDateTime(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
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
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BookOpen className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Formations</p>
              <p className="text-2xl font-bold">{stats.total_courses}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Calendar className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Sessions a venir</p>
              <p className="text-2xl font-bold">{stats.upcoming_sessions}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Users className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Participants</p>
              <p className="text-2xl font-bold">{stats.total_participants}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Award className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Certificats</p>
              <p className="text-2xl font-bold">{stats.certificates_issued}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// COURSES TAB (Catalogue)
// ============================================================================

function CoursesTab() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<TrainingType | ''>('');

  const { data, isLoading } = useCourseList({
    search: search || undefined,
    training_type: typeFilter || undefined,
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
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          value={typeFilter}
          onValueChange={(value) => setTypeFilter(value as TrainingType | '')}
        >
          <option value="">Tous les types</option>
          {Object.entries(TRAINING_TYPE_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle formation
        </Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((course) => (
            <Card key={course.id} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="p-4">
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
                  <Badge variant="outline">
                    {TRAINING_TYPE_CONFIG[course.training_type]?.label || course.training_type}
                  </Badge>
                  <Badge variant="outline">
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

                <Button className="w-full mt-4" variant="outline">
                  Voir les sessions
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<BookOpen className="h-12 w-12" />}
          title="Aucune formation"
          description="Creez votre premiere formation pour commencer."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer une formation
            </Button>
          }
        />
      )}
    </div>
  );
}

// ============================================================================
// SESSIONS TAB
// ============================================================================

function SessionsTab() {
  const [statusFilter, setStatusFilter] = useState<SessionStatus | ''>('');

  const { data, isLoading } = useSessionList({
    status: statusFilter || undefined,
  });

  const enroll = useEnroll();

  const columns = [
    {
      header: 'Formation',
      accessorKey: 'course_name' as const,
      cell: (row: TrainingSession) => (
        <div>
          <p className="font-medium">{row.course_name}</p>
          <p className="text-sm text-muted-foreground">Session: {row.code}</p>
        </div>
      ),
    },
    {
      header: 'Dates',
      accessorKey: 'start_date' as const,
      cell: (row: TrainingSession) => (
        <div>
          <p>{formatDate(row.start_date)}</p>
          {row.end_date && row.end_date !== row.start_date && (
            <p className="text-sm text-muted-foreground">au {formatDate(row.end_date)}</p>
          )}
        </div>
      ),
    },
    {
      header: 'Lieu',
      accessorKey: 'location' as const,
      cell: (row: TrainingSession) => (
        <div className="flex items-center gap-1">
          {row.is_virtual ? <Video className="h-4 w-4" /> : <MapPin className="h-4 w-4" />}
          <span>{row.is_virtual ? 'En ligne' : row.location || '-'}</span>
        </div>
      ),
    },
    {
      header: 'Formateur',
      accessorKey: 'trainer_name' as const,
    },
    {
      header: 'Places',
      accessorKey: 'enrolled_count' as const,
      cell: (row: TrainingSession) => (
        <span>
          {row.enrolled_count || 0}/{row.max_participants}
        </span>
      ),
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: TrainingSession) => <SessionStatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: (row: TrainingSession) => (
        <div className="flex gap-2">
          {row.status === 'open' && (row.enrolled_count || 0) < row.max_participants && (
            <Button
              size="sm"
              onClick={() => enroll.mutate({ session_id: row.id })}
            >
              S'inscrire
            </Button>
          )}
          <Button size="sm" variant="outline">
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
          onValueChange={(value) => setStatusFilter(value as SessionStatus | '')}
          className="w-48"
        >
          <option value="">Tous les statuts</option>
          {Object.entries(SESSION_STATUS_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
        <Button className="ml-auto">
          <Plus className="h-4 w-4 mr-2" />
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
          description="Planifiez votre premiere session de formation."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Planifier une session
            </Button>
          }
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

  const columns = [
    {
      header: 'Formateur',
      accessorKey: 'name' as const,
      cell: (row: Trainer) => (
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
      header: 'Specialisation',
      accessorKey: 'specialization' as const,
    },
    {
      header: 'Type',
      accessorKey: 'is_internal' as const,
      cell: (row: Trainer) => (
        <Badge variant={row.is_internal ? 'default' : 'outline'}>
          {row.is_internal ? 'Interne' : 'Externe'}
        </Badge>
      ),
    },
    {
      header: 'Tarif journalier',
      accessorKey: 'daily_rate' as const,
      cell: (row: Trainer) => row.daily_rate ? `${toNum(row.daily_rate).toFixed(0)} EUR` : '-',
    },
    {
      header: 'Note moyenne',
      accessorKey: 'average_rating' as const,
      cell: (row: Trainer) => row.average_rating ? `${toNum(row.average_rating).toFixed(1)}/5` : '-',
    },
    {
      header: 'Statut',
      accessorKey: 'is_active' as const,
      cell: (row: Trainer) => (
        <Badge variant={row.is_active ? 'default' : 'outline'}>
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
        description="Ajoutez vos formateurs pour pouvoir planifier des sessions."
        action={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Ajouter un formateur
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
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

  const columns = [
    {
      header: 'Formation',
      accessorKey: 'course_name' as const,
      cell: (row: Enrollment) => (
        <div>
          <p className="font-medium">{row.course_name}</p>
          <p className="text-sm text-muted-foreground">Session: {row.session_code}</p>
        </div>
      ),
    },
    {
      header: 'Date',
      accessorKey: 'session_start_date' as const,
      cell: (row: Enrollment) => formatDate(row.session_start_date),
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: Enrollment) => <EnrollmentStatusBadge status={row.status} />,
    },
    {
      header: 'Progression',
      accessorKey: 'progress_percent' as const,
      cell: (row: Enrollment) => (
        <div className="w-32">
          <Progress value={row.progress_percent || 0} />
          <p className="text-xs text-muted-foreground mt-1">{row.progress_percent || 0}%</p>
        </div>
      ),
    },
    {
      header: 'Presence',
      accessorKey: 'attendance_rate' as const,
      cell: (row: Enrollment) => `${row.attendance_rate || 0}%`,
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: (row: Enrollment) => (
        <div className="flex gap-2">
          {row.status === 'enrolled' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => cancelEnrollment.mutate(row.id)}
            >
              Annuler
            </Button>
          )}
          {row.status === 'in_progress' && (
            <Button size="sm">
              <Play className="h-4 w-4 mr-1" />
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
        description="Vous n'etes inscrit a aucune formation pour le moment."
        action={
          <Button>
            <BookOpen className="h-4 w-4 mr-2" />
            Voir le catalogue
          </Button>
        }
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
        description="Completez des formations pour obtenir vos certificats."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {certificates.map((cert) => (
        <Card key={cert.id} className="border-2 border-dashed">
          <CardContent className="p-6 text-center">
            <Award className="h-12 w-12 mx-auto text-yellow-500 mb-4" />
            <h3 className="font-bold text-lg">{cert.course_name}</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Delivre le {formatDate(cert.issued_at)}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              N° {cert.certificate_number}
            </p>
            {cert.score !== undefined && (
              <Badge className="mt-3">
                Score: {cert.score}%
              </Badge>
            )}
            <div className="flex gap-2 mt-4 justify-center">
              <Button size="sm" variant="outline">
                Telecharger
              </Button>
              <Button size="sm" variant="outline">
                Verifier
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
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
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
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
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <GraduationCap className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Formation</h1>
            <p className="text-muted-foreground">
              Gestion des formations, sessions et certifications
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nouvelle formation
          </Button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Main Content */}
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
  );
}

// Named exports
export { TrainingModule };
export * from './types';
export * from './hooks';
export * from './api';
export { trainingMeta } from './meta';
