/**
 * AZALSCORE - Demo Video Component
 * Présentation animée avec synthèse vocale automatique
 * Utilise Web Speech API pour la voix off en français
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Play, Pause, Square, Volume2, VolumeX, RotateCcw, SkipForward, SkipBack } from 'lucide-react';

// ============================================================
// CONFIGURATION DES SLIDES
// ============================================================

interface Slide {
  title: string;
  subtitle: string;
  description: string;
  image: string;
  voiceText: string;
  pitch?: number;   // Variation de hauteur pour cette slide
  rate?: number;    // Variation de débit pour cette slide
  duration: number;
}

const SLIDES: Slide[] = [
  {
    title: "AZALSCORE",
    subtitle: "L'ERP français pour les PME",
    description: "Simplifiez votre gestion au quotidien",
    image: "/screenshots/landing.png",
    voiceText: "Bienvenue. Découvrez Azalscore. L'ERP français, conçu pour les PME. Simplifiez votre gestion au quotidien.",
    pitch: 1.0,
    rate: 0.85,
    duration: 10000,
  },
  {
    title: "Cockpit Dirigeant",
    subtitle: "Pilotez votre entreprise",
    description: "Tous vos indicateurs clés en un coup d'œil",
    image: "/screenshots/module-cockpit.png",
    voiceText: "Le Cockpit Dirigeant. Visualisez en un instant, votre chiffre d'affaires, votre trésorerie, et vos factures. Tout est centralisé.",
    pitch: 1.0,
    rate: 0.85,
    duration: 10000,
  },
  {
    title: "Facturation Électronique",
    subtitle: "Conforme 2026 • Factur-X",
    description: "Devis et factures professionnels en quelques clics",
    image: "/screenshots/module-devis.png",
    voiceText: "La Facturation. Créez vos devis et factures en quelques clics. Déjà conforme à la réglementation 2026. Format Factur-X inclus.",
    pitch: 1.0,
    rate: 0.85,
    duration: 10000,
  },
  {
    title: "CRM Intégré",
    subtitle: "Gestion relation client",
    description: "Historique complet, relances automatiques, pipeline de ventes",
    image: "/screenshots/module-crm.png",
    voiceText: "Le CRM intégré. Gérez vos clients et vos prospects. Historique complet, relances automatiques, et pipeline de ventes visuel.",
    pitch: 1.0,
    rate: 0.85,
    duration: 10000,
  },
  {
    title: "Gestion des Stocks",
    subtitle: "Inventaire en temps réel",
    description: "Multi-entrepôts, alertes, traçabilité complète",
    image: "/screenshots/module-inventory.png",
    voiceText: "La Gestion des Stocks. Suivez votre inventaire en temps réel. Multi-entrepôts, alertes de réapprovisionnement, traçabilité complète.",
    pitch: 1.0,
    rate: 0.85,
    duration: 10000,
  },
  {
    title: "Trésorerie",
    subtitle: "Maîtrisez vos finances",
    description: "Encaissements, prévisions, rapprochement bancaire",
    image: "/screenshots/module-treasury.png",
    voiceText: "La Trésorerie. Maîtrisez vos flux financiers. Encaissements, prévisions, et rapprochement bancaire automatique.",
    pitch: 1.0,
    rate: 0.85,
    duration: 10000,
  },
  {
    title: "Essayez Gratuitement",
    subtitle: "100% Français • RGPD • Hébergé en France",
    description: "30 jours d'essai sur azalscore.com",
    image: "/screenshots/real-interface.png",
    voiceText: "Azalscore. 100% français, hébergé en France, conforme RGPD. Essayez gratuitement pendant 30 jours, sur azalscore point com.",
    pitch: 1.0,
    rate: 0.82,
    duration: 11000,
  },
];

// ============================================================
// HOOK POUR LA SYNTHÈSE VOCALE
// ============================================================

const useSpeechSynthesis = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);

      const loadVoices = () => {
        const availableVoices = speechSynthesis.getVoices();
        setVoices(availableVoices);
      };

      loadVoices();
      speechSynthesis.addEventListener('voiceschanged', loadVoices);

      return () => {
        speechSynthesis.removeEventListener('voiceschanged', loadVoices);
        speechSynthesis.cancel();
      };
    }
  }, []);

  const getFrenchVoice = useCallback((): SpeechSynthesisVoice | null => {
    // Chercher une voix française de qualité
    const frenchVoices = voices.filter(v => v.lang.startsWith('fr'));

    // Debug: afficher les voix disponibles
    if (frenchVoices.length > 0) {
      console.log('Voix françaises disponibles:', frenchVoices.map(v => `${v.name} (${v.lang})`));
    }

    // Priorité aux voix Google (plus naturelles)
    const googleVoice = frenchVoices.find(v =>
      v.name.includes('Google') ||
      v.name.includes('google')
    );
    if (googleVoice) return googleVoice;

    // Ensuite les voix Microsoft
    const microsoftVoice = frenchVoices.find(v =>
      v.name.includes('Microsoft') ||
      v.name.includes('Hortense') ||
      v.name.includes('Julie') ||
      v.name.includes('Paul')
    );
    if (microsoftVoice) return microsoftVoice;

    // Voix Apple de qualité
    const appleVoice = frenchVoices.find(v =>
      v.name.includes('Thomas') ||
      v.name.includes('Amelie') ||
      v.name.includes('Audrey') ||
      v.name.includes('Enhanced') ||
      v.name.includes('Premium')
    );
    if (appleVoice) return appleVoice;

    return frenchVoices[0] || null;
  }, [voices]);

  const speak = useCallback((text: string, pitch: number = 1.0, rate: number = 0.9, onEnd?: () => void): void => {
    if (!isSupported) {
      onEnd?.();
      return;
    }

    // Arrêter toute parole en cours
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const frenchVoice = getFrenchVoice();

    if (frenchVoice) {
      utterance.voice = frenchVoice;
    }

    utterance.lang = 'fr-FR';
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      onEnd?.();
    };
    utterance.onerror = (e) => {
      console.warn('Speech error:', e);
      setIsSpeaking(false);
      onEnd?.();
    };

    utteranceRef.current = utterance;
    speechSynthesis.speak(utterance);
  }, [isSupported, getFrenchVoice]);

  const stop = useCallback(() => {
    if (isSupported) {
      speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [isSupported]);

  const pause = useCallback(() => {
    if (isSupported && isSpeaking) {
      speechSynthesis.pause();
    }
  }, [isSupported, isSpeaking]);

  const resume = useCallback(() => {
    if (isSupported) {
      speechSynthesis.resume();
    }
  }, [isSupported]);

  return { isSupported, isSpeaking, speak, stop, pause, resume, voices };
};

// ============================================================
// COMPOSANT SLIDESHOW AVEC VOIX
// ============================================================

const DemoVideo: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [slideProgress, setSlideProgress] = useState(0);

  const { isSupported: speechSupported, speak, stop: stopSpeech } = useSpeechSynthesis();
  const slideStartTime = useRef<number>(0);
  const animationFrame = useRef<number>(0);
  const isWaitingForSpeech = useRef(false);

  const totalDuration = SLIDES.reduce((acc, s) => acc + s.duration, 0);

  const formatTime = (ms: number): string => {
    const secs = Math.floor(ms / 1000);
    const mins = Math.floor(secs / 60);
    return `${mins}:${(secs % 60).toString().padStart(2, '0')}`;
  };

  const getElapsedTime = useCallback(() => {
    let time = 0;
    for (let i = 0; i < currentSlide; i++) {
      time += SLIDES[i].duration;
    }
    if (isPlaying && slideStartTime.current > 0) {
      const slideElapsed = Math.min(
        Date.now() - slideStartTime.current,
        SLIDES[currentSlide].duration
      );
      time += slideElapsed;
    }
    return time;
  }, [currentSlide, isPlaying]);

  // Animation loop pour la progression
  useEffect(() => {
    if (!isPlaying) {
      cancelAnimationFrame(animationFrame.current);
      return;
    }

    const animate = () => {
      const elapsed = Date.now() - slideStartTime.current;
      const slideDuration = SLIDES[currentSlide].duration;
      const slidePercent = Math.min((elapsed / slideDuration) * 100, 100);
      setSlideProgress(slidePercent);

      const totalElapsed = getElapsedTime();
      setProgress((totalElapsed / totalDuration) * 100);

      // Passer à la slide suivante si la durée est écoulée ET la voix a fini
      if (elapsed >= slideDuration && !isWaitingForSpeech.current) {
        if (currentSlide < SLIDES.length - 1) {
          setCurrentSlide(prev => prev + 1);
        } else {
          // Fin de la présentation
          setIsPlaying(false);
          setCurrentSlide(0);
          setProgress(0);
          setSlideProgress(0);
          return;
        }
      }

      animationFrame.current = requestAnimationFrame(animate);
    };

    animationFrame.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame.current);
  }, [isPlaying, currentSlide, getElapsedTime, totalDuration]);

  // Lancer la voix quand la slide change
  useEffect(() => {
    if (!isPlaying) return;

    slideStartTime.current = Date.now();
    setSlideProgress(0);

    if (!isMuted && speechSupported) {
      isWaitingForSpeech.current = true;
      const slide = SLIDES[currentSlide];
      speak(slide.voiceText, slide.pitch ?? 1.0, slide.rate ?? 0.9, () => {
        isWaitingForSpeech.current = false;
      });
    }
  }, [currentSlide, isPlaying, isMuted, speechSupported, speak]);

  const handlePlay = () => {
    if (isPlaying) {
      // Pause
      setIsPlaying(false);
      stopSpeech();
    } else {
      // Play
      if (currentSlide === SLIDES.length - 1 && progress >= 99) {
        // Recommencer depuis le début
        setCurrentSlide(0);
        setProgress(0);
      }
      slideStartTime.current = Date.now();
      setIsPlaying(true);
    }
  };

  const handleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    if (newMuted) {
      stopSpeech();
    } else if (isPlaying) {
      // Relancer la voix de la slide actuelle
      const slide = SLIDES[currentSlide];
      speak(slide.voiceText, slide.pitch ?? 1.0, slide.rate ?? 0.9);
    }
  };

  const handleStop = () => {
    stopSpeech();
    setIsPlaying(false);
    setCurrentSlide(0);
    setProgress(0);
    setSlideProgress(0);
  };

  const handleRestart = () => {
    stopSpeech();
    setCurrentSlide(0);
    setProgress(0);
    setSlideProgress(0);
    slideStartTime.current = Date.now();
    setIsPlaying(true);
  };

  const handlePrev = () => {
    if (currentSlide > 0) {
      stopSpeech();
      setCurrentSlide(prev => prev - 1);
      slideStartTime.current = Date.now();
    }
  };

  const handleNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      stopSpeech();
      setCurrentSlide(prev => prev + 1);
      slideStartTime.current = Date.now();
    }
  };

  const goToSlide = (index: number) => {
    stopSpeech();
    setCurrentSlide(index);
    slideStartTime.current = Date.now();

    // Calculer la progression
    let time = 0;
    for (let i = 0; i < index; i++) time += SLIDES[i].duration;
    setProgress((time / totalDuration) * 100);
  };

  const slide = SLIDES[currentSlide];

  return (
    <div className="demo-video-container">
      <div className="demo-video-player demo-video-slideshow">
        {/* Écran principal */}
        <div className="demo-video-screen">
          <div className="demo-video-slide" key={currentSlide}>
            <img
              src={slide.image}
              alt={slide.title}
              className="demo-video-image"
              loading="eager"
            />
            <div className="demo-video-overlay demo-video-overlay--slideshow">
              <div className="demo-video-slide-content">
                <span className="demo-video-slide-number">
                  {currentSlide + 1} / {SLIDES.length}
                </span>
                <h3 className="demo-video-slide-title">{slide.title}</h3>
                <p className="demo-video-slide-subtitle">{slide.subtitle}</p>
                <p className="demo-video-slide-description">{slide.description}</p>
              </div>
            </div>

            {/* Barre de progression de la slide */}
            {isPlaying && (
              <div className="demo-video-slide-progress">
                <div
                  className="demo-video-slide-progress-fill"
                  style={{ width: `${slideProgress}%` }}
                />
              </div>
            )}
          </div>

          {/* Overlay de lecture */}
          {!isPlaying && (
            <div className="demo-video-play-overlay" onClick={handlePlay}>
              <div className="demo-video-play-button">
                <Play size={56} fill="white" />
              </div>
              <span className="demo-video-play-label">
                {speechSupported ? 'Lancer la présentation avec voix' : 'Lancer la présentation'}
              </span>
              <span className="demo-video-duration-badge">
                {formatTime(totalDuration)}
              </span>
              {!speechSupported && (
                <span className="demo-video-no-speech">
                  Votre navigateur ne supporte pas la synthèse vocale
                </span>
              )}
            </div>
          )}
        </div>

        {/* Contrôles - toujours visibles */}
        <div className="demo-video-controls visible">
          {/* Temps et progression */}
          <div className="demo-video-time-display">
            <span className="demo-video-time-current">{formatTime(getElapsedTime())}</span>
            <div className="demo-video-progress-container">
              <div className="demo-video-progress-bar">
                <div
                  className="demo-video-progress-fill"
                  style={{ width: `${progress}%` }}
                />
                {/* Marqueurs de slides */}
                <div className="demo-video-progress-markers">
                  {SLIDES.map((_, idx) => {
                    let pos = 0;
                    for (let i = 0; i < idx; i++) pos += SLIDES[i].duration;
                    const percent = (pos / totalDuration) * 100;
                    return (
                      <div
                        key={idx}
                        className={`demo-video-progress-marker ${idx === currentSlide ? 'active' : ''}`}
                        style={{ left: `${percent}%` }}
                        onClick={() => goToSlide(idx)}
                        title={`Slide ${idx + 1}: ${SLIDES[idx].title}`}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
            <span className="demo-video-time-total">{formatTime(totalDuration)}</span>
          </div>

          {/* Boutons de contrôle */}
          <div className="demo-video-buttons">
            <div className="demo-video-buttons-left">
              {/* Play/Pause */}
              <button
                onClick={handlePlay}
                className="demo-video-btn demo-video-btn-primary"
                aria-label={isPlaying ? 'Pause' : 'Lecture'}
                title={isPlaying ? 'Pause' : 'Lecture'}
              >
                {isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>

              {/* Stop */}
              <button
                onClick={handleStop}
                className="demo-video-btn"
                aria-label="Arrêter"
                title="Arrêter"
              >
                <Square size={20} />
              </button>

              {/* Restart */}
              <button
                onClick={handleRestart}
                className="demo-video-btn"
                aria-label="Recommencer"
                title="Recommencer"
              >
                <RotateCcw size={20} />
              </button>

              <div className="demo-video-separator" />

              {/* Navigation */}
              <button
                onClick={handlePrev}
                className="demo-video-btn"
                disabled={currentSlide === 0}
                aria-label="Slide précédente"
                title="Précédent"
              >
                <SkipBack size={20} />
              </button>

              <button
                onClick={handleNext}
                className="demo-video-btn"
                disabled={currentSlide === SLIDES.length - 1}
                aria-label="Slide suivante"
                title="Suivant"
              >
                <SkipForward size={20} />
              </button>

              <div className="demo-video-separator" />

              {/* Son */}
              <button
                onClick={handleMute}
                className={`demo-video-btn ${isMuted ? 'demo-video-btn-muted' : ''}`}
                aria-label={isMuted ? 'Activer la voix' : 'Couper la voix'}
                title={isMuted ? 'Activer la voix' : 'Couper la voix'}
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
            </div>

            {/* Indicateur de slide */}
            <div className="demo-video-slide-indicator">
              <span>Slide {currentSlide + 1} / {SLIDES.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Badge son */}
      <div className="demo-video-badge">
        <span>{isMuted ? '🔇 Son coupé' : '🎙️ Voix FR'}</span>
      </div>
    </div>
  );
};

export default DemoVideo;
