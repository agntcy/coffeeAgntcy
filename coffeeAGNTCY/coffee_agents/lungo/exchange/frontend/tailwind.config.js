/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			'primary-bg': '#23282E',
  			'primary-blue': '#187ADC',
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		spacing: {
  			'122': '122px',
  			'160': '160px',
  			'162': '162px',
  			'166': '166px',
  			'194': '194px',
  			'269': '269px'
  		},
  		width: {
  			'122': '122px',
  			'160': '160px',
  			'162': '162px',
  			'166': '166px',
  			'194': '194px',
  			'269': '269px'
  		},
  		height: {
  			'96': '96px'
  		},
  		colors: {
  			'node-bg': '#373C42',
  			'node-hover': '#4A4F55',
  			'icon-bg': '#59616B',
  			'node-text': '#E8E9EA',
  			'action-bg': '#00142B',
  			'action-border': '#187ADC'
  		},
  		fontFamily: {
  			cisco: [
  				'CiscoSansTT',
  				'Inter'
  			],
  			inter: [
  				'Inter'
  			]
  		},
  		animation: {
  			fadeInDropdown: 'fadeInDropdown 0.3s ease-out',
  			scaleIn: 'scaleIn 0.25s ease-in-out'
  		},
  		keyframes: {
  			fadeInDropdown: {
  				from: {
  					opacity: '0',
  					transform: 'translateY(10px)'
  				},
  				to: {
  					opacity: '1',
  					transform: 'translateY(0)'
  				}
  			},
  			scaleIn: {
  				from: {
  					transform: 'scale(0.3)'
  				},
  				to: {
  					transform: 'scale(1)'
  				}
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
