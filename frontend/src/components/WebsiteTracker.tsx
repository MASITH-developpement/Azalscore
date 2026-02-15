import { useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('azals_session');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('azals_session', sessionId);
  }
  return sessionId;
};

export const WebsiteTracker = () => {
  useEffect(() => {
    const trackVisit = async () => {
      try {
        const sessionId = getSessionId();
        const urlParams = new URLSearchParams(window.location.search);

        await fetch(`${API_URL}/api/website/track-visit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            landing_page: window.location.pathname,
            current_page: window.location.pathname,
            referrer: document.referrer || null,
            user_agent: navigator.userAgent,
            device_type: /Mobile|Android|iPhone/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            utm_source: urlParams.get('utm_source'),
            utm_medium: urlParams.get('utm_medium'),
            utm_campaign: urlParams.get('utm_campaign'),
          }),
        });
      } catch (error) {
        // Silently fail - tracking should not break the app
        console.debug('Tracking error:', error);
      }
    };

    trackVisit();

    const handlePageView = () => {
      trackVisit();
    };

    window.addEventListener('popstate', handlePageView);
    return () => window.removeEventListener('popstate', handlePageView);
  }, []);

  return null;
};

export default WebsiteTracker;
