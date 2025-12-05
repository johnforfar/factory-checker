import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic'; // Force dynamic rendering
export const revalidate = 0; // Disable caching

export async function GET() {
  try {
    const cwd = process.cwd();
    const possibleStatePaths = [
      path.join(cwd, 'apps-state.json'),
      path.join(cwd, 'app-review', 'apps-state.json'),
    ];
    
    // Note: We don't check appsDir anymore to prevent Next.js from analyzing public/apps files
    // Files in public/ are served as static assets and don't need filesystem checks
    
    let stateFile = possibleStatePaths.find(file => fs.existsSync(file)) || possibleStatePaths[0];
    
    if (!fs.existsSync(stateFile)) {
      return NextResponse.json({ error: 'State file not found' }, { status: 404 });
    }
    
    const appsState = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    
    // Build app data WITHOUT filesystem checks to prevent Next.js from bundling image files
    // Files in public/ are served as static assets and don't need filesystem checks
    const apps = Object.keys(appsState).map(appName => {
      const state = appsState[appName];
      
      let screenshots: string[] = [];
      let icon: string | null = null;
      
      // Infer screenshot existence from state data (same logic as page component)
      // Don't use fs.readdirSync() or fs.statSync() - this causes Next.js to bundle all files
      const hasScreenshotAnalysis = !!state.screenshot_analysis;
      const hasLastChecked = !!state.last_checked && state.last_checked !== 'Never';
      const isActiveOrDefault = state.status === 'Active' || state.status === 'Default';
      
      // If any indicator suggests screenshots exist, include them
      // Browser will handle missing images gracefully
      if (hasScreenshotAnalysis || (hasLastChecked && isActiveOrDefault)) {
        screenshots = ['screenshot-1.png'];
        icon = `/apps/${appName}/logo.png`; // Most apps use logo.png (not icon.png)
      }
      
      return {
        name: appName,
        title: state.title || appName,
        status: state.status || 'Pending',
        screenshots,
        icon,
        lastUpdated: state.last_updated || null,
        lastChecked: state.last_checked || null,
        lastCheckedRaw: state.last_checked,
        commit: state.commit_hash || state.last_assessed_hash || null,
        commits: state.commits || 0,
        builder: state.builder || null,
        prompt: state.prompt || null,
        prompts: state.prompts || (state.prompt ? [{ type: 'Initial', text: state.prompt }] : null),
        rawDate: state.last_updated,
        screenshotAnalysis: state.screenshot_analysis || null,
        description: state.description || null,
      };
    });
    
    return NextResponse.json({ apps });
  } catch (error) {
    console.error('Error in apps API route:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

