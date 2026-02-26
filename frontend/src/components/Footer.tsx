/**
 * AZALSCORE - Footer Component
 * Composant de pied de page réutilisable pour toutes les pages publiques
 */

import React from 'react';
import { Link } from 'react-router-dom';

interface FooterProps {
  variant?: 'full' | 'simple';
}

export const Footer: React.FC<FooterProps> = ({ variant = 'full' }) => {
  if (variant === 'simple') {
    return (
      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold text-blue-400">AZALSCORE</span>
              <span className="text-gray-400 text-sm">ERP SaaS français</span>
            </div>
            <nav className="flex flex-wrap justify-center gap-4 text-sm text-gray-400">
              <Link to="/mentions-legales" className="hover:text-white">Mentions légales</Link>
              <Link to="/confidentialite" className="hover:text-white">Confidentialité</Link>
              <Link to="/cgv" className="hover:text-white">CGV</Link>
              <Link to="/contact" className="hover:text-white">Contact</Link>
            </nav>
          </div>
          <p className="text-center text-gray-500 text-sm mt-4">
            &copy; 2026 AZALSCORE - MASITH Développement. Tous droits réservés.
          </p>
        </div>
      </footer>
    );
  }

  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="max-w-6xl mx-auto px-4">
        <div className="grid md:grid-cols-5 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link to="/" className="text-2xl font-bold text-blue-400 hover:text-blue-300">
              AZALSCORE
            </Link>
            <p className="text-gray-400 text-sm mt-2">
              L'ERP français pour les PME modernes
            </p>
          </div>

          {/* Produit */}
          <div>
            <h4 className="font-semibold mb-4">Produit</h4>
            <nav className="flex flex-col gap-2 text-sm text-gray-400">
              <Link to="/features" className="hover:text-white">Fonctionnalités</Link>
              <Link to="/pricing" className="hover:text-white">Tarifs</Link>
              <Link to="/essai-gratuit" className="hover:text-white">Essai gratuit</Link>
              <Link to="/demo" className="hover:text-white">Demander une démo</Link>
            </nav>
          </div>

          {/* Secteurs */}
          <div>
            <h4 className="font-semibold mb-4">Secteurs</h4>
            <nav className="flex flex-col gap-2 text-sm text-gray-400">
              <Link to="/secteurs/commerce" className="hover:text-white">Commerce & Retail</Link>
              <Link to="/secteurs/services" className="hover:text-white">Services</Link>
              <Link to="/secteurs/industrie" className="hover:text-white">Industrie</Link>
            </nav>
          </div>

          {/* Ressources */}
          <div>
            <h4 className="font-semibold mb-4">Ressources</h4>
            <nav className="flex flex-col gap-2 text-sm text-gray-400">
              <Link to="/blog" className="hover:text-white">Blog</Link>
              <Link to="/blog/facturation-electronique-2026" className="hover:text-white">Facturation 2026</Link>
              <Link to="/blog/erp-pme-guide-complet" className="hover:text-white">Guide ERP</Link>
              <Link to="/comparatif" className="hover:text-white">Comparatifs ERP</Link>
            </nav>
          </div>

          {/* Entreprise */}
          <div>
            <h4 className="font-semibold mb-4">Entreprise</h4>
            <nav className="flex flex-col gap-2 text-sm text-gray-400">
              <Link to="/contact" className="hover:text-white">Contact</Link>
              <Link to="/mentions-legales" className="hover:text-white">Mentions légales</Link>
              <Link to="/confidentialite" className="hover:text-white">Confidentialité</Link>
              <Link to="/cgv" className="hover:text-white">CGV</Link>
            </nav>
          </div>
        </div>

        {/* Bottom */}
        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-400 text-sm">
              &copy; 2026 AZALSCORE - MASITH Développement. Tous droits réservés.
            </p>
            <p className="text-gray-500 text-sm">
              ERP SaaS français • Hébergé en France • Conforme RGPD • Facturation 2026
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
