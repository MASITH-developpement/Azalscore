export const StructuredData = () => {
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareApplication",
        "name": "Azalscore ERP",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web, Windows, macOS, Linux",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "EUR"
        },
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": "4.9",
          "ratingCount": "156"
        },
        "softwareVersion": "2.0",
        "description": "ERP open-source complet pour PME avec CRM, comptabilité, inventaire, RH, POS et plus. Architecture multi-tenant moderne.",
        "featureList": "CRM, Comptabilité, Gestion de Stock, RH, Point de Vente, Service Terrain, Trésorerie, Multi-tenant, API REST",
        "url": "https://azalscore.com",
        "downloadUrl": "https://github.com/MASITH-developpement/Azalscore",
        "screenshot": "https://azalscore.com/screenshot.png",
        "maintainer": {
          "@type": "Organization",
          "name": "MASITH Développement"
        }
      },
      {
        "@type": "Organization",
        "name": "MASITH Développement",
        "url": "https://azalscore.com",
        "logo": "https://azalscore.com/logo.png",
        "sameAs": [
          "https://github.com/MASITH-developpement",
          "https://www.linkedin.com/company/azalscore"
        ],
        "contactPoint": {
          "@type": "ContactPoint",
          "contactType": "customer support",
          "email": "contact@azalscore.com",
          "availableLanguage": ["French", "English"]
        }
      },
      {
        "@type": "WebSite",
        "name": "Azalscore ERP",
        "url": "https://azalscore.com",
        "potentialAction": {
          "@type": "SearchAction",
          "target": "https://azalscore.com/search?q={search_term_string}",
          "query-input": "required name=search_term_string"
        }
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
