// PlantVillage label helpers (mirror of model/labels.py).

export function splitLabel(label = '') {
  if (!label.includes('___')) return ['Plant', label.replaceAll('_', ' ').trim()]
  const [crop, disease] = label.split('___')
  return [crop.replaceAll('_', ' ').trim(), disease.replaceAll('_', ' ').trim()]
}

export function formatLabel(label = '') {
  if (!label.includes('___')) return label.replaceAll('_', ' ')
  const [crop, disease] = splitLabel(label)
  return `${crop} — ${disease}`
}

export const extractCrop = (label = '') => label.split('___')[0].replaceAll('_', ' ')
export const isHealthy = (label = '') => label.toLowerCase().includes('healthy')

export const CROP_COLORS = {
  Apple: '#dc2626',
  Blueberry: '#4f46e5',
  'Cherry (including sour)': '#be185d',
  'Corn (maize)': '#ca8a04',
  Grape: '#7c3aed',
  Orange: '#ea580c',
  Peach: '#f97316',
  'Pepper, bell': '#16a34a',
  Potato: '#92400e',
  Raspberry: '#e11d48',
  Soybean: '#65a30d',
  Squash: '#d97706',
  Strawberry: '#f43f5e',
  Tomato: '#b91c1c',
}
