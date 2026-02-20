/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      /* ============================================================
         AZALSCORE Design Tokens Integration
         Permet l'utilisation des classes Tailwind avec les tokens CSS
         Exemple: bg-azals-primary, text-azals-gray-600, etc.
         ============================================================ */
      colors: {
        azals: {
          // Primary (Charte AZALSCORE: #1E6EFF)
          primary: {
            50: 'var(--azals-primary-50)',
            100: 'var(--azals-primary-100)',
            200: 'var(--azals-primary-200)',
            300: 'var(--azals-primary-300)',
            400: 'var(--azals-primary-400)',
            500: 'var(--azals-primary-500)',
            600: 'var(--azals-primary-600)',
            700: 'var(--azals-primary-700)',
            800: 'var(--azals-primary-800)',
            900: 'var(--azals-primary-900)',
            DEFAULT: 'var(--azals-primary-500)',
          },
          // Semantic
          success: 'var(--azals-success)',
          warning: 'var(--azals-warning)',
          danger: 'var(--azals-danger)',
          info: 'var(--azals-info)',
          // Neutral
          gray: {
            50: 'var(--azals-gray-50)',
            100: 'var(--azals-gray-100)',
            200: 'var(--azals-gray-200)',
            300: 'var(--azals-gray-300)',
            400: 'var(--azals-gray-400)',
            500: 'var(--azals-gray-500)',
            600: 'var(--azals-gray-600)',
            700: 'var(--azals-gray-700)',
            800: 'var(--azals-gray-800)',
            900: 'var(--azals-gray-900)',
          },
          // Alert
          red: {
            DEFAULT: 'var(--azals-red)',
            light: 'var(--azals-red-light)',
            800: 'var(--azals-red-800)',
          },
          orange: {
            DEFAULT: 'var(--azals-orange)',
            light: 'var(--azals-orange-light)',
          },
          green: {
            DEFAULT: 'var(--azals-green)',
            light: 'var(--azals-green-light)',
            100: 'var(--azals-green-100)',
          },
          // Extended palette
          violet: {
            500: 'var(--azals-violet-500)',
            600: 'var(--azals-violet-600)',
            700: 'var(--azals-violet-700)',
          },
          indigo: {
            500: 'var(--azals-indigo-500)',
          },
          pink: {
            50: 'var(--azals-pink-50)',
            500: 'var(--azals-pink-500)',
            600: 'var(--azals-pink-600)',
            800: 'var(--azals-pink-800)',
          },
          amber: {
            100: 'var(--azals-amber-100)',
            600: 'var(--azals-amber-600)',
            700: 'var(--azals-amber-700)',
            800: 'var(--azals-amber-800)',
            900: 'var(--azals-amber-900)',
          },
          // Semantic backgrounds
          bg: 'var(--azals-bg)',
          'bg-secondary': 'var(--azals-bg-secondary)',
          text: 'var(--azals-text)',
          'text-secondary': 'var(--azals-text-secondary)',
          border: 'var(--azals-border)',
        },
      },
      fontFamily: {
        sans: ['var(--azals-font-family)'],
        mono: ['var(--azals-font-mono)'],
        serif: ['var(--azals-font-serif)'],
      },
      fontSize: {
        'azals-xs': 'var(--azals-font-size-xs)',
        'azals-sm': 'var(--azals-font-size-sm)',
        'azals-md': 'var(--azals-font-size-md)',
        'azals-lg': 'var(--azals-font-size-lg)',
        'azals-xl': 'var(--azals-font-size-xl)',
        'azals-2xl': 'var(--azals-font-size-2xl)',
        'azals-3xl': 'var(--azals-font-size-3xl)',
      },
      spacing: {
        'azals-xs': 'var(--azals-spacing-xs)',
        'azals-sm': 'var(--azals-spacing-sm)',
        'azals-md': 'var(--azals-spacing-md)',
        'azals-lg': 'var(--azals-spacing-lg)',
        'azals-xl': 'var(--azals-spacing-xl)',
        'azals-2xl': 'var(--azals-spacing-2xl)',
      },
      borderRadius: {
        'azals-sm': 'var(--azals-radius-sm)',
        'azals-md': 'var(--azals-radius-md)',
        'azals-lg': 'var(--azals-radius-lg)',
        'azals-xl': 'var(--azals-radius-xl)',
        'azals-full': 'var(--azals-radius-full)',
      },
      boxShadow: {
        'azals-sm': 'var(--azals-shadow-sm)',
        'azals-md': 'var(--azals-shadow-md)',
        'azals-lg': 'var(--azals-shadow-lg)',
      },
      transitionDuration: {
        'azals-fast': '150ms',
        'azals-normal': '200ms',
        'azals-slow': '300ms',
      },
      zIndex: {
        'azals-sidebar-overlay': 'var(--azals-z-sidebar-overlay)',
        'azals-sidebar': 'var(--azals-z-sidebar)',
        'azals-banner': 'var(--azals-z-banner)',
        'azals-header': 'var(--azals-z-header)',
        'azals-popover': 'var(--azals-z-popover)',
        'azals-dropdown': 'var(--azals-z-dropdown)',
        'azals-modal': 'var(--azals-z-modal)',
        'azals-toast': 'var(--azals-z-toast)',
        'azals-quick-create': 'var(--azals-z-quick-create)',
        'azals-palette': 'var(--azals-z-palette)',
        'azals-guardian': 'var(--azals-z-guardian)',
      },
    },
  },
  plugins: [],
}
