/**
 * AZALSCORE - Page À propos
 */

import React from 'react';
import { PageWrapper, Card } from '@ui/layout';
import { AzalscoreLogo } from '@/components/Logo';
import { Shield, Server, Users, Award } from 'lucide-react';

const AboutPage: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <PageWrapper title="À propos" subtitle="Informations sur AZALSCORE">
      <div className="azals-about">
        {/* Logo et présentation */}
        <Card className="azals-about__hero">
          <div className="azals-about__hero-content">
            <div className="azals-about__logo">
              <AzalscoreLogo size="2xl" variant="full" alt="AZALSCORE" />
            </div>
            <div className="azals-about__description">
              <h2>ERP SaaS Enterprise</h2>
              <p>
                AZALSCORE est une plateforme ERP SaaS de nouvelle génération,
                conçue pour répondre aux exigences des entreprises modernes.
                Solution complète de gestion d'entreprise, sécurisée et conforme
                aux standards les plus stricts.
              </p>
            </div>
          </div>
        </Card>

        {/* Informations techniques */}
        <div className="azals-about__grid">
          <Card title="Version">
            <div className="azals-about__info">
              <p><strong>Version :</strong> 1.0.0</p>
              <p><strong>Build :</strong> Production</p>
              <p><strong>Dernière mise à jour :</strong> Janvier {currentYear}</p>
            </div>
          </Card>

          <Card title="Éditeur">
            <div className="azals-about__info">
              <p><strong>Société :</strong> MASITH</p>
              <p><strong>Siège :</strong> France</p>
              <p><strong>Contact :</strong> contact@masith.com</p>
            </div>
          </Card>
        </div>

        {/* Points forts */}
        <Card title="Caractéristiques">
          <div className="azals-about__features">
            <div className="azals-about__feature">
              <div className="azals-about__feature-icon">
                <Shield size={24} />
              </div>
              <div>
                <h4>Sécurité Enterprise</h4>
                <p>Chiffrement AES-256, authentification multi-facteurs, audit complet</p>
              </div>
            </div>
            <div className="azals-about__feature">
              <div className="azals-about__feature-icon">
                <Server size={24} />
              </div>
              <div>
                <h4>Infrastructure Cloud</h4>
                <p>Haute disponibilité, sauvegarde automatique, scalabilité</p>
              </div>
            </div>
            <div className="azals-about__feature">
              <div className="azals-about__feature-icon">
                <Users size={24} />
              </div>
              <div>
                <h4>Multi-tenant</h4>
                <p>Isolation des données, personnalisation par organisation</p>
              </div>
            </div>
            <div className="azals-about__feature">
              <div className="azals-about__feature-icon">
                <Award size={24} />
              </div>
              <div>
                <h4>Conformité</h4>
                <p>RGPD, normes comptables françaises, audit trail complet</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Mentions légales */}
        <Card title="Mentions légales">
          <div className="azals-about__legal">
            <p>
              &copy; {currentYear} MASITH. Tous droits réservés.
            </p>
            <p>
              AZALSCORE est une marque déposée. Toute reproduction ou utilisation
              non autorisée est strictement interdite.
            </p>
            <div className="azals-about__legal-links">
              <a href="/legal/privacy">Politique de confidentialité</a>
              <a href="/legal/terms">Conditions d'utilisation</a>
              <a href="/legal/security">Politique de sécurité</a>
            </div>
          </div>
        </Card>

        {/* Footer avec logo */}
        <div className="azals-about__footer">
          <AzalscoreLogo size="sm" variant="horizontal" />
        </div>
      </div>
    </PageWrapper>
  );
};

export default AboutPage;
