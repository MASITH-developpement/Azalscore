/**
 * AZALSCORE - MainLayout Wrapper
 * Re-export du UnifiedLayout pour compatibilité
 */

import React from 'react';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children, title }) => {
  return (
    <div className="azals-main-layout">
      {title && (
        <div className="azals-main-layout__header">
          <h1 className="azals-main-layout__title">{title}</h1>
        </div>
      )}
      <div className="azals-main-layout__content">
        {children}
      </div>
    </div>
  );
};

export default MainLayout;
