import animate from 'tailwindcss-animate';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        clinical: {
          50:  'var(--ds-clinical-50)',
          100: 'var(--ds-clinical-100)',
          200: 'var(--ds-clinical-200)',
          300: 'var(--ds-clinical-300)',
          400: 'var(--ds-clinical-400)',
          500: 'var(--ds-clinical-500)',
          600: 'var(--ds-clinical-600)',
          700: 'var(--ds-clinical-700)',
          800: 'var(--ds-clinical-800)',
          900: 'var(--ds-clinical-900)',
        },
        action: {
          50:  'var(--ds-action-50)',
          100: 'var(--ds-action-100)',
          200: 'var(--ds-action-200)',
          300: 'var(--ds-action-300)',
          400: 'var(--ds-action-400)',
          500: 'var(--ds-action-500)',
          600: 'var(--ds-action-600)',
          700: 'var(--ds-action-700)',
          800: 'var(--ds-action-800)',
          900: 'var(--ds-action-900)',
        },
        accent: {
          50:  'var(--ds-accent-50)',
          100: 'var(--ds-accent-100)',
          200: 'var(--ds-accent-200)',
          300: 'var(--ds-accent-300)',
          400: 'var(--ds-accent-400)',
          500: 'var(--ds-accent-500)',
          600: 'var(--ds-accent-600)',
          700: 'var(--ds-accent-700)',
          800: 'var(--ds-accent-800)',
          900: 'var(--ds-accent-900)',
          DEFAULT: 'var(--ds-accent-500)',
          foreground: 'var(--ds-clinical-50)',
        },
        border:      'hsl(var(--ds-border) / <alpha-value>)',
        input:       'hsl(var(--ds-input) / <alpha-value>)',
        ring:        'hsl(var(--ds-ring) / <alpha-value>)',
        background:  'var(--color-bg-canvas)',
        foreground:  'var(--color-text-primary)',
        primary: {
          DEFAULT:    'hsl(var(--ds-primary) / <alpha-value>)',
          foreground: 'hsl(var(--ds-primary-foreground) / <alpha-value>)',
        },
        secondary: {
          DEFAULT:    'hsl(var(--ds-secondary) / <alpha-value>)',
          foreground: 'hsl(var(--ds-secondary-foreground) / <alpha-value>)',
        },
        destructive: {
          DEFAULT:    'hsl(var(--ds-destructive) / <alpha-value>)',
          foreground: 'hsl(var(--ds-destructive-foreground) / <alpha-value>)',
        },
        muted: {
          DEFAULT:    'hsl(var(--ds-muted) / <alpha-value>)',
          foreground: 'hsl(var(--ds-muted-foreground) / <alpha-value>)',
        },
        popover: {
          DEFAULT:    'hsl(var(--ds-popover) / <alpha-value>)',
          foreground: 'hsl(var(--ds-popover-foreground) / <alpha-value>)',
        },
        card: {
          DEFAULT:    'hsl(var(--ds-card) / <alpha-value>)',
          foreground: 'hsl(var(--ds-card-foreground) / <alpha-value>)',
        },
      },
      borderRadius: {
        lg: 'var(--radius-lg)',
        md: 'var(--radius-md)',
        sm: 'var(--radius-sm)',
      },
      boxShadow: {
        xs:    'var(--shadow-xs)',
        sm:    'var(--shadow-sm)',
        md:    'var(--shadow-md)',
        lg:    'var(--shadow-lg)',
        xl:    'var(--shadow-xl)',
        '2xl': 'var(--shadow-2xl)',
      },
    },
  },
  plugins: [animate],
};
