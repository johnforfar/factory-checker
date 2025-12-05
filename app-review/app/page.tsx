import fs from 'fs';
import path from 'path';
import DashboardClient from './dashboard-client';

// Force dynamic rendering to prevent bundling public/apps files
export const dynamic = 'force-dynamic';
export const revalidate = 0;

// Market Rubric Definitions
const RUBRIC = {
  visualPolish: "UI/UX design quality, custom styling vs templates",
  interactivity: "Responsiveness to user input",
  assetQuality: "Image/Icon resolution and relevance",
  functionalityDepth: "Complexity of logic (games, scoring, etc.)",
  vibeCheck: "Overall fun/utility factor"
};

// Read CSV to get descriptions and categories
function readCSVData() {
  // Try multiple possible paths for the CSV file
  const possiblePaths = [
    path.join(process.cwd(), 'app-review', 'apps.csv'), // If running from root
    path.join(process.cwd(), 'apps.csv'), // If running from app-review directory
  ];
  
  let csvFile = null;
  for (const possiblePath of possiblePaths) {
    if (fs.existsSync(possiblePath)) {
      csvFile = possiblePath;
      break;
    }
  }
  
  const csvData = new Map();
  
  if (csvFile) {
    try {
      const csvContent = fs.readFileSync(csvFile, 'utf-8');
      const lines = csvContent.split('\n');
      if (lines.length > 1) {
        // Parse header
        const headerLine = lines[0];
        const headers = [];
        let currentHeader = '';
        let inQuotes = false;
        for (let i = 0; i < headerLine.length; i++) {
          const char = headerLine[i];
          if (char === '"') {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            headers.push(currentHeader.trim());
            currentHeader = '';
          } else {
            currentHeader += char;
          }
        }
        headers.push(currentHeader.trim());
        
        const nameIndex = headers.indexOf('name');
        const descIndex = headers.indexOf('description');
        const categoriesIndex = headers.indexOf('categories');
        
        // Parse data rows
        for (let i = 1; i < lines.length; i++) {
          if (!lines[i].trim()) continue;
          
          // Parse CSV line (handling quoted values with commas)
          const values = [];
          let current = '';
          inQuotes = false;
          for (let j = 0; j < lines[i].length; j++) {
            const char = lines[i][j];
            if (char === '"') {
              inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
              // Remove surrounding quotes if present
              const cleaned = current.trim().replace(/^"|"$/g, '');
              values.push(cleaned);
              current = '';
            } else {
              current += char;
            }
          }
          // Add last value
          const cleaned = current.trim().replace(/^"|"$/g, '');
          values.push(cleaned);
          
          if (nameIndex >= 0 && values[nameIndex]) {
            const name = values[nameIndex];
            csvData.set(name, {
              description: descIndex >= 0 && values[descIndex] ? values[descIndex] : null,
              categories: categoriesIndex >= 0 && values[categoriesIndex] ? values[categoriesIndex] : null
            });
          }
        }
      }
    } catch (e) {
      console.error('Error reading CSV:', e);
      // Don't break the page if CSV reading fails - just return empty map
    }
  } else {
    console.warn('CSV file not found at any of these paths:', possiblePaths);
  }
  
  return csvData;
}

export default function Page() {
  // Try multiple possible paths for state file (Next.js might run from app-review or root directory)
  // On Vercel, paths might be different - try various locations
  const cwd = process.cwd();
  const possibleStatePaths = [
    path.join(cwd, 'apps-state.json'), // If running from app-review directory
    path.join(cwd, 'app-review', 'apps-state.json'), // If running from root directory
    path.join(cwd, '..', 'apps-state.json'), // Vercel might use different structure
    path.join('/vercel/path0', 'apps-state.json'), // Vercel deployment path
  ];
  
  // Find state file (we still need this for app data)
  let stateFile = possibleStatePaths.find(file => fs.existsSync(file)) || possibleStatePaths[0];
  
  // Note: We don't check appsDir anymore to prevent Next.js from analyzing public/apps files
  // Files in public/ are served as static assets and don't need filesystem checks
  console.log('Current working directory:', cwd);
  console.log('Using stateFile:', stateFile);
  console.log('StateFile exists:', stateFile ? fs.existsSync(stateFile) : false);
  
  let apps = [];
  let appsState = {};

  try {
    // Read CSV data (non-blocking - if it fails, continue without it)
    let csvData = new Map();
    try {
      csvData = readCSVData();
      if (csvData.size > 0) {
        console.log(`Loaded ${csvData.size} apps from CSV with descriptions/categories`);
      }
    } catch (csvError) {
      console.warn('Warning: Failed to load CSV data:', csvError);
      // Continue without CSV data - descriptions will come from metadata.ts
    }
    
    console.log('Looking for state file at:', stateFile);
    if (fs.existsSync(stateFile)) {
        appsState = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
        console.log(`Loaded ${Object.keys(appsState).length} apps from state file`);
    } else {
        console.error('State file not found at any of these paths:', possibleStatePaths);
    }

    // Drive from state file to show ALL apps, even those without local assets yet
    apps = Object.keys(appsState).map(appName => {
        const state = appsState[appName];
        
        let screenshots = [];
        let icon = null;

        // Don't check filesystem at build/runtime - this causes Next.js to bundle all files
        // Instead, infer file existence from state data and let browser handle 404s
        // Files in public/ are served as static assets and don't need filesystem checks
        
        // Infer screenshot existence from multiple state indicators:
        // 1. screenshot_analysis exists (most reliable)
        // 2. last_checked exists (indicates app was processed and likely has screenshots)
        // 3. status is Active/Default (more likely to have screenshots than Pending)
        // We'll assume common file names exist - browser will handle 404s gracefully
        const hasScreenshotAnalysis = !!state.screenshot_analysis;
        const hasLastChecked = !!state.last_checked && state.last_checked !== 'Never';
        const isActiveOrDefault = state.status === 'Active' || state.status === 'Default';
        
        // If any indicator suggests screenshots exist, include them
        // This is a best-effort approach - SafeThumbnailImage handles missing files
        if (hasScreenshotAnalysis || (hasLastChecked && isActiveOrDefault)) {
            screenshots = ['screenshot-1.png'];
            // Try logo.png first (most common), then icon.png as fallback
            // The browser will handle 404s gracefully
            icon = `/apps/${appName}/logo.png`; // Most apps use logo.png
        }
        
        // Note: We're not using fs.readdirSync() or fs.statSync() here to prevent
        // Next.js from analyzing and bundling all files from public/apps/
        // The browser will handle missing images gracefully via the SafeThumbnailImage component
        // Images are served as static assets from public/apps/ by Vercel automatically

        // Get description and categories from CSV (preferred), then fallback to metadata.ts
        // csvData is defined in the outer scope - handle case where it might not be available
        const csvInfo = (csvData && csvData.get) ? csvData.get(appName) : null;
        let description = csvInfo?.description || state.description || null;
        let categories = csvInfo?.categories || null;
        
        // Parse categories string into array
        let categoriesArray = [];
        if (categories && categories.trim()) {
            // Handle both comma-separated and space-separated categories
            categoriesArray = categories.split(/[,\s]+/)
                .map(c => c.trim())
                .filter(c => c.length > 0);
        }
        
        if (!description) {
            try {
                const metadataPath = path.join(process.cwd(), 'apps', appName, 'mini-app', 'lib', 'metadata.ts');
                if (fs.existsSync(metadataPath)) {
                    const metadataContent = fs.readFileSync(metadataPath, 'utf8');
                    // Extract description from export const description = "..." or `...`
                    // Handle both single-line and multi-line strings
                    const singleLineMatch = metadataContent.match(/export\s+const\s+description\s*=\s*["']([^"'`]+)["']/);
                    const multiLineMatch = metadataContent.match(/export\s+const\s+description\s*=\s*`([^`]+)`/s);
                    if (singleLineMatch && singleLineMatch[1]) {
                        description = singleLineMatch[1].trim();
                    } else if (multiLineMatch && multiLineMatch[1]) {
                        // For multi-line, take first line or first sentence
                        const firstLine = multiLineMatch[1].split('\n')[0].trim();
                        // If first line is very long, take first sentence
                        if (firstLine.length > 150) {
                            const firstSentence = firstLine.split(/[.!?]/)[0].trim();
                            description = firstSentence || firstLine.substring(0, 150).trim();
                        } else {
                            description = firstLine;
                        }
                    }
                }
            } catch (e) {
                // Silently fail if metadata.ts doesn't exist or can't be read
            }
        }

        // Helper to format date
        const formatDate = (val) => {
            if (!val) return 'Never';
            if (typeof val === 'number' || !isNaN(val)) {
                return new Date(val * 1000).toLocaleDateString() + ' ' + new Date(val * 1000).toLocaleTimeString();
            }
            try {
                return new Date(val).toLocaleDateString() + ' ' + new Date(val).toLocaleTimeString();
            } catch (e) { return String(val); }
        };

        return {
            name: appName,
            title: state.title || appName,
            description: description,
            categories: categoriesArray,
            status: state.status || 'Pending',
            screenshots,
            icon,
            lastUpdated: formatDate(state.last_updated),
            lastChecked: formatDate(state.last_checked),
            lastCheckedRaw: state.last_checked, // Raw for relative time
            commit: state.commit_hash || state.last_assessed_hash || null,
            commits: state.commits || 0,
            builder: state.builder || null,
            prompt: state.prompt || null, // Single prompt for backward compatibility
            prompts: state.prompts || (state.prompt ? [{ type: 'Initial', text: state.prompt }] : null), // Array of prompts
            rawDate: state.last_updated, // For sorting
            screenshotAnalysis: state.screenshot_analysis || null // Screenshot quality analysis
        };
    });

    // Calculate quality score and assign fixed ranks
    const calculateQualityScore = (app) => {
        let score = 0;
        
        // Commits: logarithmic scale (more commits = better, but diminishing returns)
        // Score: log10(commits + 1) * 20, capped at 50 points
        const commits = app.commits || 0;
        score += Math.min(Math.log10(commits + 1) * 20, 50);
        
        // Status: Active = 30, Default = 10, Pending = 0
        if (app.status === 'Active') score += 30;
        else if (app.status === 'Default') score += 10;
        
        // Has screenshots: 15 points (quality assessment done)
        if (app.screenshots && app.screenshots.length > 0) {
            score += 15;
            
            // Add visual quality bonus from screenshot analysis (0-25 points)
            // Visual quality is 0-100, we scale it to 0-25 points
            const screenshotAnalysis = app.screenshotAnalysis;
            if (screenshotAnalysis && screenshotAnalysis.visual_quality !== null && screenshotAnalysis.visual_quality !== undefined) {
                const visualQuality = screenshotAnalysis.visual_quality;
                score += Math.round((visualQuality / 100) * 25); // Scale 0-100 to 0-25 points
                
                // Bonus for custom content (not default template)
                if (screenshotAnalysis.has_custom_content === true) {
                    score += 5;
                }
            }
        }
        
        // Has icon: 10 points (completeness)
        if (app.icon) score += 10;
        
        // Has description: 10 points (completeness)
        if (app.description && app.description.trim().length > 0) score += 10;
        
        // Has prompts: 10 points (user engagement)
        if (app.prompts && app.prompts.length > 0) score += 10;
        
        // Recent update bonus: up to 10 points
        if (app.rawDate) {
            try {
                const date = typeof app.rawDate === 'string' ? new Date(app.rawDate) : new Date(app.rawDate * 1000);
                const daysSinceUpdate = (new Date() - date) / (1000 * 60 * 60 * 24);
                if (daysSinceUpdate < 7) score += 10;
                else if (daysSinceUpdate < 30) score += 5;
                else if (daysSinceUpdate < 90) score += 2;
            } catch (e) {
                // Invalid date, skip bonus
            }
        }
        
        // Has last checked: 5 points (data completeness)
        if (app.lastCheckedRaw && app.lastCheckedRaw !== 'Never') score += 5;
        
        return score;
    };

    // Calculate scores and assign ranks
    const appsWithScores = apps.map(app => ({
        ...app,
        qualityScore: calculateQualityScore(app)
    }));

    // Sort by quality score (descending), then by name for tie-breaking
    appsWithScores.sort((a, b) => {
        if (b.qualityScore !== a.qualityScore) {
            return b.qualityScore - a.qualityScore;
        }
        return a.name.localeCompare(b.name);
    });

    // Assign fixed ranks (1-based)
    const appsWithRanks = appsWithScores.map((app, index) => ({
        ...app,
        rank: index + 1
    }));

    // Create a map of name -> rank for quick lookup
    const rankMap = new Map();
    appsWithRanks.forEach(app => {
        rankMap.set(app.name, app.rank);
    });

    // Add rank to original apps array
    apps = apps.map(app => ({
        ...app,
        rank: rankMap.get(app.name) || 9999 // Default rank for apps not in map
    }));

  } catch (e) {
    console.error("Error reading apps directory or state:", e);
    console.error("Error stack:", e.stack);
    // Ensure we return something even if there's an error
    if (apps.length === 0) {
      console.error("No apps loaded! Check state file and CSV file paths.");
    }
  }

  console.log(`Rendering dashboard with ${apps.length} apps`);
  return <DashboardClient apps={apps} rubric={RUBRIC} />;
}
