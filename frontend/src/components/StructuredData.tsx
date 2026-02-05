export const StructuredData = () => {
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareApplication",
        "name": "Azalscore ERP",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": {
          "@type": "Offer",
          "price": "49",
          "priceCurrency": "EUR",
          "priceValidUntil": "2026-12-31",
          "availability": "https://schema.org/InStock"
        },
        "softwareVersion": "2.0",
        "description": "ERP SaaS francais pour PME : CRM, comptabilite, facturation electronique 2026, inventaire, RH, POS. Conforme RGPD, heberge en France.",
        "featureList": "CRM, Comptabilite, Facturation electronique, Gestion de Stock, RH, Point de Vente, Tresorerie, Multi-tenant, API REST, RGPD",
        "url": "https://azalscore.com",
        "screenshot": "https://azalscore.com/og-image.png",
        "maintainer": {
          "@type": "Organization",
          "name": "MASITH Developpement"
        },
        "applicationSuite": "AZALSCORE",
        "countriesSupported": "FR"
      },
      {
        "@type": "Organization",
        "name": "MASITH Developpement",
        "url": "https://azalscore.com",
        "logo": "https://azalscore.com/pwa-512x512.png",
        "contactPoint": {
          "@type": "ContactPoint",
          "contactType": "customer support",
          "email": "contact@azalscore.com",
          "availableLanguage": ["French"]
        },
        "address": {
          "@type": "PostalAddress",
          "addressCountry": "FR"
        }
      },
      {
        "@type": "WebSite",
        "name": "Azalscore ERP",
        "url": "https://azalscore.com",
        "inLanguage": "fr-FR"
      }
    ]
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
    />
  );
};

export default StructuredData;
