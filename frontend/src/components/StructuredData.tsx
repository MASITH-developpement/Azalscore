/**
 * AZALSCORE - Structured Data (Schema.org)
 * Rich snippets pour SEO - Google, Bing, etc.
 */

export const StructuredData = () => {
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      // Application Software
      {
        "@type": "SoftwareApplication",
        "@id": "https://azalscore.com/#software",
        "name": "Azalscore ERP",
        "applicationCategory": "BusinessApplication",
        "applicationSubCategory": "Enterprise Resource Planning",
        "operatingSystem": "Web, iOS, Android",
        "offers": {
          "@type": "AggregateOffer",
          "lowPrice": "29",
          "highPrice": "499",
          "priceCurrency": "EUR",
          "offerCount": "3",
          "offers": [
            {
              "@type": "Offer",
              "name": "Starter",
              "price": "29",
              "priceCurrency": "EUR",
              "priceValidUntil": "2027-12-31",
              "availability": "https://schema.org/InStock",
              "url": "https://azalscore.com/pricing#starter"
            },
            {
              "@type": "Offer",
              "name": "Business",
              "price": "79",
              "priceCurrency": "EUR",
              "priceValidUntil": "2027-12-31",
              "availability": "https://schema.org/InStock",
              "url": "https://azalscore.com/pricing#business"
            },
            {
              "@type": "Offer",
              "name": "Enterprise",
              "price": "499",
              "priceCurrency": "EUR",
              "priceValidUntil": "2027-12-31",
              "availability": "https://schema.org/InStock",
              "url": "https://azalscore.com/pricing#enterprise"
            }
          ]
        },
        "softwareVersion": "2.0",
        "releaseNotes": "https://azalscore.com/docs/changelog",
        "description": "ERP SaaS francais pour PME : CRM, comptabilite, facturation electronique 2026, inventaire, RH, POS. Conforme RGPD, heberge en France.",
        "featureList": [
          "CRM et gestion de la relation client",
          "Facturation electronique conforme 2026",
          "Comptabilite en partie double",
          "Gestion de stock et inventaire",
          "Ressources humaines et paie",
          "Point de vente (POS)",
          "Tresorerie et rapprochement bancaire",
          "Multi-tenant et multi-devises",
          "API REST documentee",
          "Conforme RGPD"
        ],
        "url": "https://azalscore.com",
        "downloadUrl": "https://azalscore.com/essai-gratuit",
        "screenshot": "https://azalscore.com/og-image.png",
        "maintainer": {
          "@type": "Organization",
          "name": "MASITH Developpement"
        },
        "publisher": {
          "@type": "Organization",
          "name": "MASITH Developpement"
        },
        "applicationSuite": "AZALSCORE",
        "countriesSupported": ["FR", "BE", "CH", "LU", "MC"],
        "availableLanguage": ["fr"],
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": "4.8",
          "ratingCount": "127",
          "bestRating": "5",
          "worstRating": "1"
        },
        "review": [
          {
            "@type": "Review",
            "author": {
              "@type": "Person",
              "name": "Marie D."
            },
            "reviewRating": {
              "@type": "Rating",
              "ratingValue": "5"
            },
            "reviewBody": "Excellent ERP, tres complet et simple a utiliser. Le support est reactif."
          }
        ]
      },

      // Organization
      {
        "@type": "Organization",
        "@id": "https://azalscore.com/#organization",
        "name": "MASITH Developpement",
        "legalName": "MASITH Developpement SAS",
        "url": "https://azalscore.com",
        "logo": {
          "@type": "ImageObject",
          "url": "https://azalscore.com/pwa-512x512.png",
          "width": 512,
          "height": 512
        },
        "image": "https://azalscore.com/og-image.png",
        "email": "contact@azalscore.com",
        "contactPoint": [
          {
            "@type": "ContactPoint",
            "contactType": "customer support",
            "email": "support@azalscore.com",
            "availableLanguage": ["French"],
            "areaServed": ["FR", "BE", "CH", "LU"]
          },
          {
            "@type": "ContactPoint",
            "contactType": "sales",
            "email": "contact@azalscore.com",
            "availableLanguage": ["French"]
          }
        ],
        "address": {
          "@type": "PostalAddress",
          "addressCountry": "FR",
          "addressLocality": "France"
        },
        "sameAs": [
          "https://www.linkedin.com/company/azalscore",
          "https://twitter.com/azalscore"
        ],
        "foundingDate": "2024",
        "numberOfEmployees": {
          "@type": "QuantitativeValue",
          "minValue": 2,
          "maxValue": 10
        }
      },

      // WebSite with SearchAction
      {
        "@type": "WebSite",
        "@id": "https://azalscore.com/#website",
        "name": "Azalscore ERP",
        "url": "https://azalscore.com",
        "inLanguage": "fr-FR",
        "publisher": {
          "@id": "https://azalscore.com/#organization"
        },
        "potentialAction": {
          "@type": "SearchAction",
          "target": {
            "@type": "EntryPoint",
            "urlTemplate": "https://azalscore.com/search?q={search_term_string}"
          },
          "query-input": "required name=search_term_string"
        }
      },

      // WebPage (Homepage)
      {
        "@type": "WebPage",
        "@id": "https://azalscore.com/#webpage",
        "url": "https://azalscore.com",
        "name": "Azalscore ERP - Logiciel de Gestion d'Entreprise Francais",
        "description": "ERP SaaS francais pour PME : CRM, Comptabilite, Inventaire, RH, POS. Solution cloud securisee, hebergee en France, conforme RGPD.",
        "inLanguage": "fr-FR",
        "isPartOf": {
          "@id": "https://azalscore.com/#website"
        },
        "about": {
          "@id": "https://azalscore.com/#software"
        },
        "primaryImageOfPage": {
          "@type": "ImageObject",
          "url": "https://azalscore.com/og-image.png"
        },
        "breadcrumb": {
          "@type": "BreadcrumbList",
          "itemListElement": [
            {
              "@type": "ListItem",
              "position": 1,
              "name": "Accueil",
              "item": "https://azalscore.com"
            }
          ]
        }
      },

      // FAQ Page
      {
        "@type": "FAQPage",
        "@id": "https://azalscore.com/#faq",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "Qu'est-ce qu'Azalscore ERP ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Azalscore est un ERP SaaS francais complet pour les PME. Il integre la gestion commerciale (CRM, devis, factures), la comptabilite, la gestion de stock, les ressources humaines, la tresorerie et bien plus. Solution 100% francaise, hebergee en France et conforme RGPD."
            }
          },
          {
            "@type": "Question",
            "name": "Azalscore est-il conforme a la facturation electronique 2026 ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Oui, Azalscore est entierement conforme aux exigences de la facturation electronique 2026 en France. Le logiciel supporte les formats Factur-X, l'envoi via PDP (Plateforme de Dematerialisation Partenaire) et l'archivage legal des factures."
            }
          },
          {
            "@type": "Question",
            "name": "Combien coute Azalscore ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Azalscore propose 3 formules : Starter a 29 euros/mois HT pour les TPE (1-3 utilisateurs), Business a 79 euros/mois HT pour les PME en croissance (5-15 utilisateurs), et Enterprise sur devis pour les grandes structures (utilisateurs illimites). Un essai gratuit de 30 jours est disponible."
            }
          },
          {
            "@type": "Question",
            "name": "Mes donnees sont-elles securisees ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Absolument. Vos donnees sont hebergees exclusivement en France, chiffrees avec AES-256, et l'acces est protege par authentification 2FA. Nous sommes conformes RGPD et nos systemes sont audites regulierement. Chaque client beneficie d'une isolation complete de ses donnees (architecture multi-tenant)."
            }
          },
          {
            "@type": "Question",
            "name": "Puis-je importer mes donnees existantes ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Oui, Azalscore permet l'import de donnees depuis Excel, CSV et d'autres ERP. Notre equipe peut vous accompagner dans la migration de vos donnees clients, produits, factures et historiques."
            }
          },
          {
            "@type": "Question",
            "name": "Y a-t-il une API pour integrer Azalscore ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Oui, Azalscore dispose d'une API REST complete et documentee (OpenAPI/Swagger). Vous pouvez integrer l'ERP avec vos outils existants, votre site e-commerce, ou developper des automatisations personnalisees."
            }
          },
          {
            "@type": "Question",
            "name": "Le support est-il inclus ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Oui, tous les plans incluent un support par email. Les plans Business et Enterprise beneficient d'un support prioritaire avec des temps de reponse garantis. Le plan Enterprise inclut un support 24/7 dedie."
            }
          },
          {
            "@type": "Question",
            "name": "Puis-je annuler mon abonnement a tout moment ?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Oui, Azalscore fonctionne sans engagement. Vous pouvez annuler votre abonnement a tout moment depuis votre espace client. Vos donnees restent accessibles pendant 30 jours apres l'annulation pour vous permettre de les exporter."
            }
          }
        ]
      },

      // Product (for e-commerce visibility)
      {
        "@type": "Product",
        "@id": "https://azalscore.com/#product",
        "name": "Azalscore ERP",
        "description": "Logiciel ERP SaaS francais pour PME",
        "brand": {
          "@type": "Brand",
          "name": "Azalscore"
        },
        "category": "Logiciel de gestion d'entreprise",
        "image": "https://azalscore.com/og-image.png",
        "offers": {
          "@type": "Offer",
          "price": "29",
          "priceCurrency": "EUR",
          "availability": "https://schema.org/InStock",
          "priceValidUntil": "2027-12-31",
          "url": "https://azalscore.com/pricing",
          "seller": {
            "@id": "https://azalscore.com/#organization"
          }
        },
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": "4.8",
          "reviewCount": "127"
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
