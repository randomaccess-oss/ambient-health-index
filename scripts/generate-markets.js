#!/usr/bin/env node

/**
 * Ambient Health Index — Market Data Generator
 *
 * This script aggregates publicly available data to generate
 * condition scores for each US market. Data sources:
 *
 * - Temporal Synchronization: BLS office occupancy, CBRE hybrid work reports
 * - Spatial Concentration: Census density, Walk Score API, Census CBP (bar counts)
 * - Low Planning Cost: Census CBP (NAICS 7224), transit accessibility
 * - Social Permission: State alcohol culture indices, per-capita consumption
 * - Repetition: Census CBP establishment tenure, population stability (Census ACS)
 *
 * To wire up real data sources:
 * 1. Add API keys to GitHub Secrets (WALK_SCORE_API_KEY, etc.)
 * 2. Implement fetch functions for each data source
 * 3. Map raw data to 0-100 scores using the normalization functions below
 * 4. Generate notes from the raw data context
 *
 * For now, this script reads the existing markets.json and validates it.
 */

const fs = require('fs');
const path = require('path');

const OUTPUT_PATH = path.join(__dirname, '..', 'markets.json');

// Placeholder: read existing data and validate
function validate() {
  const raw = fs.readFileSync(OUTPUT_PATH, 'utf8');
  const data = JSON.parse(raw);

  console.log(`Loaded ${data.markets.length} markets`);

  const conditions = ['temporal', 'spatial', 'planning', 'permission', 'repetition'];
  let errors = 0;

  data.markets.forEach(m => {
    conditions.forEach(c => {
      if (!m.conditions[c]) {
        console.error(`Missing condition ${c} for ${m.city}, ${m.state}`);
        errors++;
      } else {
        if (m.conditions[c].score < 0 || m.conditions[c].score > 100) {
          console.error(`Invalid score ${m.conditions[c].score} for ${c} in ${m.city}`);
          errors++;
        }
        if (!m.conditions[c].note || m.conditions[c].note.length === 0) {
          console.error(`Missing note for ${c} in ${m.city}`);
          errors++;
        }
      }
    });

    if (!['Mega', 'Large', 'Mid', 'Small'].includes(m.populationTier)) {
      console.error(`Invalid populationTier "${m.populationTier}" for ${m.city}`);
      errors++;
    }

    if (!['Northeast', 'Midwest', 'South', 'West'].includes(m.region)) {
      console.error(`Invalid region "${m.region}" for ${m.city}`);
      errors++;
    }
  });

  if (errors === 0) {
    console.log('Validation passed. All markets valid.');
  } else {
    console.error(`Validation failed with ${errors} errors.`);
    process.exit(1);
  }

  // Update generation date
  data.meta.generated = new Date().toISOString().split('T')[0];
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(data, null, 2));
  console.log('Updated generation date.');
}

validate();
