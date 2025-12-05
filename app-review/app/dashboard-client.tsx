'use client';

import { useState, useMemo, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

// Static list of featured apps (names)
const FEATURED_APPS = [
  'base-tic-tac-fly',
  'base-dash',
  'survival-box',
  'ai-riddle-rush',
  'do-you-thing',
  'flownest',
  'kanikani',
  'myminiapp',
  'fili-food',
  '169aac15-0af9-4d1c-bc41-dab62c049d78',
  'typhoon-preparedness-app',
  'store-smart-calculator',
  'bounty-go',
  'omega',
  'random-game',
  'win',
  'cyber-hockey',
  'number-tapping-sequence',
  'unusual-tower-de',
  'crypto-shooter',
  '2d-to-3d-printer', // Snake game with walls
  'pong',
  'base-crash',
  'brilliant',
  'xos',
  'bonfire',
  'crypto-hangman',
  'mangala'
];

/**
 * Helper function for relative time formatting.
 * 
 * IMPORTANT: This runs CLIENT-SIDE ONLY, ensuring it works correctly in any timezone.
 * - Server passes ISO strings (or Unix timestamps) as-is
 * - Client parses dates and calculates relative time using browser's local time
 * - No timezone conversion needed - works identically on localhost and Vercel
 * 
 * @param {string|number|Date} dateInput - ISO string, Unix timestamp (seconds or ms), or Date object
 * @returns {string} Relative time string (e.g., "2 hours 13 minutes ago")
 */
function formatRelativeTime(dateInput) {
  // Handle null, undefined, or string placeholders
  if (!dateInput || dateInput === 'Never' || dateInput === 'Unknown' || dateInput === '-') {
    return dateInput || 'Never';
  }
  
  let date;
  
  try {
    // Handle ISO strings (e.g., "2025-11-24T13:32:58.189428" or "2025-11-24T13:32:58Z")
    if (typeof dateInput === 'string') {
      // ISO strings are parsed correctly by Date constructor regardless of server timezone
      date = new Date(dateInput);
    } 
    // Handle Unix timestamps (seconds)
    else if (typeof dateInput === 'number') {
      // If it's less than a reasonable timestamp (before year 2000), assume it's seconds
      if (dateInput < 946684800000) { // Jan 1, 2000 in milliseconds
        date = new Date(dateInput * 1000);
      } else {
        date = new Date(dateInput); // Already milliseconds
      }
    } 
    // Handle Date objects
    else if (dateInput instanceof Date) {
      date = dateInput;
    } 
    else {
      return 'Invalid date';
    }
    
    // Validate the date
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    
    // Calculate difference using client's current time (always correct)
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    // Handle future dates (shouldn't happen, but be safe)
    if (diffMs < 0) {
      return 'just now';
    }
    
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) {
      const mins = diffMins % 60;
      return mins > 0 
        ? `${diffHours} hour${diffHours !== 1 ? 's' : ''} ${mins} minute${mins !== 1 ? 's' : ''} ago` 
        : `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    }
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    // For older dates, use locale-aware formatting (client's locale)
    return date.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  } catch (error) {
    // Fallback to original string if parsing fails
    return String(dateInput);
  }
}

export default function DashboardClient({ apps, rubric }) {
  const router = useRouter();
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedImageIndex, setSelectedImageIndex] = useState(null);
  const [screenshotList, setScreenshotList] = useState([]);
  const [imageLoading, setImageLoading] = useState(false);
  const [clickedPrompt, setClickedPrompt] = useState(null);
  const [isMounted, setIsMounted] = useState(false);
  
  // Prevent hydration mismatch - only render date-dependent content after mount
  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  // Helper function to get thumbnail path for list view
  const getThumbnailPath = (appName, screenshotName) => {
    // Remove any existing -thumb suffixes first (handle -thumb-thumb-thumb cases)
    let cleanName = screenshotName.replace(/-thumb+/g, '');
    const ext = cleanName.match(/\.(png|jpg|jpeg)$/i)?.[1] || 'png';
    const nameWithoutExt = cleanName.replace(/\.(png|jpg|jpeg)$/i, '');
    return `/apps/${appName}/${nameWithoutExt}-thumb.${ext}`;
  };
  
  // Track which images have already tried fallback to prevent infinite loops
  // Use Map to track both thumbnail and full-size failures
  const [imageLoadStates, setImageLoadStates] = useState(new Map<string, 'loading' | 'thumbnail-failed' | 'fullsize-failed' | 'loaded'>());
  
  // Safe thumbnail image component that handles missing images gracefully
  const SafeThumbnailImage = ({ 
    appName, 
    screenshotName, 
    width, 
    height, 
    style
  }: { 
    appName: string; 
    screenshotName: string; 
    width: number; 
    height: number; 
    style?: React.CSSProperties; 
  }) => {
    const imageKey = `${appName}/${screenshotName}`;
    const loadState = imageLoadStates.get(imageKey) || 'loading';
    
    // Determine which image to show
    const thumbnailPath = getThumbnailPath(appName, screenshotName);
    const fullSizePath = `/apps/${appName}/${screenshotName}`;
    
    // If thumbnail failed, use full-size; if both failed, show placeholder
    const imageSrc = loadState === 'thumbnail-failed' || loadState === 'fullsize-failed' 
      ? fullSizePath 
      : thumbnailPath;
    
    const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
      e.preventDefault(); // Prevent default error handling
      const img = e.target as HTMLImageElement;
      const currentState = imageLoadStates.get(imageKey);
      
      // Prevent infinite loops
      if (currentState === 'fullsize-failed') {
        // Both failed - hide the image gracefully
        img.style.display = 'none';
        return;
      }
      
      if (img.src.includes('-thumb') && currentState !== 'thumbnail-failed') {
        // Thumbnail failed, try full-size
        setImageLoadStates(prev => {
          const newMap = new Map(prev);
          newMap.set(imageKey, 'thumbnail-failed');
          return newMap;
        });
        // Switch to full-size image
        img.src = fullSizePath;
      } else if (!img.src.includes('-thumb')) {
        // Full-size also failed
        setImageLoadStates(prev => {
          const newMap = new Map(prev);
          newMap.set(imageKey, 'fullsize-failed');
          return newMap;
        });
        // Hide the image gracefully
        img.style.display = 'none';
      }
    };
    
    const handleLoad = () => {
      setImageLoadStates(prev => {
        const newMap = new Map(prev);
        newMap.set(imageKey, 'loaded');
        return newMap;
      });
    };
    
    // If both failed, don't render anything
    if (loadState === 'fullsize-failed') {
      return null;
    }
    
    return (
      <Image 
        src={imageSrc}
        alt={screenshotName} 
        width={width}
        height={height}
        style={style}
        loading="lazy"
        onError={handleError}
        onLoad={handleLoad}
        unoptimized={true}
      />
    );
  };
  
  // Filter States
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('⭐ Featured'); // Default to Featured
  const [activeTags, setActiveTags] = useState([]); // Array of tag IDs
  const [sortConfig, setSortConfig] = useState({ key: 'commits', direction: 'desc' });

  const openModal = (src, appName = null, screenshotName = null) => {
    // Build screenshot list from current filtered apps
    const list = [];
    filteredAndSortedApps.forEach(app => {
      if (app.screenshots && app.screenshots.length > 0) {
        app.screenshots.forEach(shot => {
          list.push({
            src: `/apps/${app.name}/${shot}`,
            appName: app.name,
            appTitle: app.title || app.name,
            screenshotName: shot
          });
        });
      }
    });

    // Find the index in the screenshot list
    const index = list.findIndex(item => 
      item.src === src || 
      (appName && screenshotName && item.appName === appName && item.screenshotName === screenshotName)
    );
    
    if (index !== -1 && list.length > 0) {
      setSelectedImageIndex(index);
      setSelectedImage(list[index]);
      setScreenshotList(list);
    } else {
      // Fallback: just set the image if not found in list
      setSelectedImage({ src, appName: appName || 'Unknown', appTitle: appName || 'Unknown', screenshotName: screenshotName || '' });
      setSelectedImageIndex(null);
      setScreenshotList([]);
    }
    setImageLoading(true);
  };

  const closeModal = () => {
    setSelectedImage(null);
    setSelectedImageIndex(null);
    setScreenshotList([]);
    setImageLoading(false);
  };

  const navigateScreenshot = (direction) => {
    if (!screenshotList.length || selectedImageIndex === null) return;
    
    let newIndex = selectedImageIndex;
    if (direction === 'up' || direction === 'prev') {
      newIndex = selectedImageIndex > 0 ? selectedImageIndex - 1 : screenshotList.length - 1;
    } else if (direction === 'down' || direction === 'next') {
      newIndex = selectedImageIndex < screenshotList.length - 1 ? selectedImageIndex + 1 : 0;
    }
    
    setSelectedImageIndex(newIndex);
    setSelectedImage(screenshotList[newIndex]);
    setImageLoading(true);
  };

  // Keyboard navigation
  useEffect(() => {
    if (!selectedImage) return;
    
    const handleKeyPress = (e) => {
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        if (screenshotList.length > 1 && selectedImageIndex !== null) {
          const newIndex = selectedImageIndex > 0 ? selectedImageIndex - 1 : screenshotList.length - 1;
          setSelectedImageIndex(newIndex);
          setSelectedImage(screenshotList[newIndex]);
          setImageLoading(true);
        }
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        if (screenshotList.length > 1 && selectedImageIndex !== null) {
          const newIndex = selectedImageIndex < screenshotList.length - 1 ? selectedImageIndex + 1 : 0;
          setSelectedImageIndex(newIndex);
          setSelectedImage(screenshotList[newIndex]);
          setImageLoading(true);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        closeModal();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedImage, selectedImageIndex, screenshotList]);

  const refreshData = () => {
      router.refresh();
  };

  // Auto-refresh every 30 seconds (reduced frequency for performance)
  useEffect(() => {
      const interval = setInterval(() => {
          router.refresh();
      }, 30000);
      return () => clearInterval(interval);
  }, [router]);


  // Map specific categories to parent categories
  const getParentCategory = (category) => {
    const categoryLower = category.toLowerCase();
    
    // Game categories -> Game
    if (['puzzle', 'quiz', 'card game', 'casino', 'platformer', 'shooter', 'classic', 'arcade'].includes(categoryLower)) {
      return 'Game';
    }
    
    // Crypto/DeFi categories -> Crypto or DeFi
    if (['defi', 'yield', 'liquidity', 'staking', 'trading', 'portfolio', 'airdrop', 'tracker', 'alert', 'calculator'].includes(categoryLower)) {
      if (['defi', 'yield', 'liquidity', 'staking'].includes(categoryLower)) {
        return 'DeFi';
      }
      return 'Crypto';
    }
    
    // AI categories -> AI
    if (['ai', 'ai chat', 'ai generator', 'generator', 'chat'].includes(categoryLower)) {
      return 'AI';
    }
    
    // Education categories -> Education
    if (['language learning', 'education'].includes(categoryLower)) {
      return 'Education';
    }
    
    // Health/Fitness categories -> Health
    if (['health', 'fitness'].includes(categoryLower)) {
      return 'Health';
    }
    
    // Social -> Social
    if (categoryLower === 'social') {
      return 'Social';
    }
    
    // Finance -> Finance
    if (categoryLower === 'finance') {
      return 'Finance';
    }
    
    // Utility -> Utility
    if (categoryLower === 'utility') {
      return 'Utility';
    }
    
    // Entertainment -> Entertainment
    if (categoryLower === 'entertainment') {
      return 'Entertainment';
    }
    
    // Other -> Other
    if (categoryLower === 'other') {
      return 'Other';
    }
    
    // Default: return the category as-is if it's already a parent category
    return category;
  };

  // Extract unique parent categories from all apps
  const parentCategories = useMemo(() => {
    const categorySet = new Set();
    apps.forEach(app => {
      if (app.categories && app.categories.length > 0) {
        app.categories.forEach(cat => {
          const parent = getParentCategory(cat);
          if (parent) {
            categorySet.add(parent);
          }
        });
      }
    });
    return Array.from(categorySet).sort();
  }, [apps]);

  // Tag definitions - grouped by mutually exclusive groups
  // Removed Commit and Updated tags for simplification as per user request
  
  // Status Filters
  const statusFilters = [
    { id: 'all', label: 'All Apps', value: 'All' },
    { id: 'featured', label: '⭐ Featured', value: '⭐ Featured' },
    { id: 'active', label: 'Active', value: 'Active' },
    { id: 'default', label: 'Default', value: 'Default' },
    { id: 'pending', label: 'Pending', value: 'Pending' },
    { id: 'completed', label: 'Check', value: 'Completed' },
    { id: 'inactive', label: 'Inactive', value: 'Inactive' },
  ];

  // Category tags - each category is independent (can select multiple)
  const categoryTags = parentCategories.map(category => ({
    id: `category-${category.toLowerCase()}`,
    label: category,
    filter: (app) => {
      if (!app.categories || app.categories.length === 0) return false;
      return app.categories.some(cat => getParentCategory(cat) === category);
    }
  }));

  // Flatten for filtering logic (only categories now)
  const availableTags = [...categoryTags];

  const toggleTag = (tagId, groupTags) => {
    setActiveTags(prev => {
      // Remove other tags from the same group - not needed for categories as they are independent
      // But we keep the logic generic if we add exclusive groups back
      
      // Toggle the selected tag
      if (prev.includes(tagId)) {
        return prev.filter(id => id !== tagId);
      } else {
        return [...prev, tagId];
      }
    });
  };

  // Find most recent update across all apps (using last_checked for data freshness)
  const { mostRecentUpdate, dataFreshness } = useMemo(() => {
    let latest = null;
    let latestChecked = null;
    
    apps.forEach(app => {
      // Check last_checked (when we last checked the app)
      if (app.lastCheckedRaw && app.lastCheckedRaw !== 'Never') {
        try {
          let checkedDate;
          if (typeof app.lastCheckedRaw === 'string') {
            checkedDate = new Date(app.lastCheckedRaw);
          } else if (typeof app.lastCheckedRaw === 'number') {
            checkedDate = app.lastCheckedRaw < 946684800000 
              ? new Date(app.lastCheckedRaw * 1000) 
              : new Date(app.lastCheckedRaw);
          }
          
          if (checkedDate && !isNaN(checkedDate.getTime())) {
            if (!latestChecked || checkedDate.getTime() > latestChecked.getTime()) {
              latestChecked = checkedDate;
            }
          }
        } catch (e) {
          // Skip invalid dates
        }
      }
      
      // Also check last_updated (GitHub update)
      if (app.rawDate) {
        try {
          let date;
          if (typeof app.rawDate === 'string') {
            date = new Date(app.rawDate);
          } else if (typeof app.rawDate === 'number') {
            date = app.rawDate < 946684800000 
              ? new Date(app.rawDate * 1000) 
              : new Date(app.rawDate);
          }
          
          if (date && !isNaN(date.getTime())) {
            if (!latest || date.getTime() > latest.getTime()) {
              latest = date;
            }
          }
        } catch (e) {
          // Skip invalid dates
        }
      }
    });
    
    // Use last_checked if available, otherwise fall back to last_updated
    const mostRecent = latestChecked || latest;
    const hoursAgo = mostRecent ? (new Date() - mostRecent.getTime()) / (1000 * 60 * 60) : Infinity;
    
    // Green if within 3 hours, red if older
    const freshness = hoursAgo <= 3 ? 'green' : 'red';
    
    return {
      mostRecentUpdate: mostRecent ? formatRelativeTime(mostRecent.toISOString()) : 'Never',
      dataFreshness: freshness
    };
  }, [apps]);

  // Filter & Sort Logic
  const filteredAndSortedApps = useMemo(() => {
    let result = [...apps];

    // 1. Filter by Status
    if (filterStatus !== 'All') {
        if (filterStatus === '⭐ Featured') {
            result = result.filter(app => FEATURED_APPS.includes(app.name));
        } else if (filterStatus === 'Completed') {
            // Filter for completed apps (status determined and checked)
            result = result.filter(app => {
                const hasStatus = app.status && app.status !== 'Pending';
                const hasChecked = app.lastChecked && app.lastChecked !== 'Never';
                return hasStatus && hasChecked;
            });
        } else {
            result = result.filter(app => app.status === filterStatus);
        }
    }

    // 3. Filter by Tags
    if (activeTags.length > 0) {
        result = result.filter(app => {
            // Separate category tags from other tags
            const categoryTagIds = activeTags.filter(id => id.startsWith('category-'));
            const otherTagIds = activeTags.filter(id => !id.startsWith('category-'));
            
            // Other tags use AND logic (all must match)
            const otherTagsMatch = otherTagIds.length === 0 || otherTagIds.every(tagId => {
                const tag = availableTags.find(t => t.id === tagId);
                return tag ? tag.filter(app) : false;
            });
            
            // Category tags use OR logic (any selected category matches)
            const categoryTagsMatch = categoryTagIds.length === 0 || categoryTagIds.some(tagId => {
                const tag = availableTags.find(t => t.id === tagId);
                return tag ? tag.filter(app) : false;
            });
            
            return otherTagsMatch && categoryTagsMatch;
        });
    }

    // 4. Filter by Search Term
    if (searchTerm) {
        const lowerTerm = searchTerm.toLowerCase();
        result = result.filter(app => 
            app.name.toLowerCase().includes(lowerTerm) || 
            (app.title && app.title.toLowerCase().includes(lowerTerm)) ||
            (app.description && app.description.toLowerCase().includes(lowerTerm))
        );
    }

    // 5. Sort
    result.sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        // Special handling for dates if sorting by lastUpdated
        if (sortConfig.key === 'lastUpdated') {
             aVal = a.rawDate || 0;
             bVal = b.rawDate || 0;
        }
        // Handle numeric sort for commits
        if (sortConfig.key === 'commits') {
             aVal = parseInt(aVal) || 0;
             bVal = parseInt(bVal) || 0;
        }
        // Handle numeric sort for rank
        if (sortConfig.key === 'rank') {
             aVal = parseInt(aVal) || 9999;
             bVal = parseInt(bVal) || 9999;
        }
        // Handle boolean sort for screenshots (has screenshots = 1, no screenshots = 0)
        if (sortConfig.key === 'screenshots') {
             aVal = (a.screenshots && a.screenshots.length > 0) ? 1 : 0;
             bVal = (b.screenshots && b.screenshots.length > 0) ? 1 : 0;
        }

        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    return result;
  }, [apps, filterStatus, searchTerm, sortConfig, activeTags]);

  // Stats
  const totalApps = apps.length;
  const defaultAppsCount = apps.filter(app => app.status === 'Default').length;
  const activeAppsCount = apps.filter(app => app.status === 'Active').length;
  const pendingAppsCount = apps.filter(app => app.status === 'Pending').length;
  const inactiveAppsCount = apps.filter(app => app.status === 'Inactive').length;
  // "Checked" means we've determined the app's status (Active/Default/Inactive)
  // and marked it as checked, regardless of whether it has icons/screenshots
  const completedAppsCount = apps.filter(app => {
      const hasStatus = app.status && app.status !== 'Pending';
      const hasChecked = app.lastChecked && app.lastChecked !== 'Never';
      return hasStatus && hasChecked;
  }).length;

  // Sort Handler
  const handleSort = (key) => {
      setSortConfig(current => ({
          key,
          direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc'
      }));
  };

  // Assessment Logic
  const assessApp = (appData) => {
    const { screenshots, status } = appData;
    const hasInteraction = screenshots.length > 1;
    
    if (status === 'Default') {
        return { vibeCheck: "FAIL - Default Template" };
    }
    if (status === 'Pending') {
        return { vibeCheck: "PENDING" };
    }
    if (status === 'Inactive') {
        return { vibeCheck: "INACTIVE" };
    }

    return {
      vibeCheck: hasInteraction ? "Verified Pass" : "Pass"
    };
  };

  return (
    <>
      <style>{`
        @media (max-width: 768px) {
          .desktop-table {
            display: none !important;
          }
          .mobile-cards {
            display: block !important;
          }
          .dashboard-container {
            padding: 12px !important;
            margin: 0 !important;
          }
          header {
            margin-bottom: 1.25rem !important;
            padding-bottom: 0.75rem !important;
          }
          header > div {
            flex-direction: column !important;
            align-items: center !important;
            text-align: center !important;
          }
          header > div > div:first-child {
            text-align: center !important;
            margin-bottom: 1rem !important;
          }
          header > div > div:last-child {
            justify-content: center !important;
          }
          .search-section {
            padding: 0.75rem !important;
            margin-bottom: 1.25rem !important;
            flex-direction: column !important;
            align-items: stretch !important;
          }
          .search-input-wrapper {
            min-width: 0 !important;
            width: 100% !important;
            margin-bottom: 0.75rem !important;
          }
          .search-input-wrapper input {
            min-width: 0 !important;
            width: 100% !important;
            box-sizing: border-box !important;
          }
          .tag-filters-section {
            flex-direction: column !important;
            align-items: flex-start !important;
          }
          .tag-filters-section > div {
            width: 100% !important;
          }
          .mobile-card {
            padding: 0.75rem !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            margin-bottom: 0.75rem !important;
          }
          .desktop-table th,
          .desktop-table td {
            padding: 0.5rem !important;
          }
          .mobile-nav-buttons {
            display: flex !important;
          }
          .desktop-nav-button {
            display: none !important;
          }
          .keyboard-hint {
            display: none !important;
          }
          section {
            padding: 0.75rem !important;
            margin-bottom: 1rem !important;
          }
          .tag-filters-section {
            padding: 0.75rem !important;
            margin-bottom: 1rem !important;
          }
          body {
            margin: 0 !important;
            padding: 0 !important;
          }
        }
        @media (min-width: 769px) {
          .desktop-table {
            display: table !important;
          }
          .mobile-cards {
            display: none !important;
          }
          .mobile-nav-buttons {
            display: none !important;
          }
          .desktop-nav-button {
            display: flex !important;
          }
          .keyboard-hint {
            display: block !important;
          }
        }
      `}</style>
    <div className="dashboard-container" style={{ maxWidth: '1600px', margin: '0 auto', position: 'relative', fontFamily: 'system-ui, sans-serif', padding: '20px' }}>
      <header style={{ marginBottom: '1.5rem', borderBottom: '2px solid #e5e7eb', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '24px' }}>
            <div style={{ flex: '1 1 auto' }}>
                <h1 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.25rem)', fontWeight: '700', margin: 0, color: '#111827', letterSpacing: '-0.02em' }}>OpenxAI Base Mini App Explorer</h1>
                <p style={{ color: '#6b7280', marginTop: '0.5rem', fontSize: '0.95rem', fontWeight: '500' }}>Quality Assessment for Vibe-Coded Apps</p>
                <p style={{ color: '#9ca3af', fontSize: '0.8125rem', marginTop: '0.5rem' }}>
                  Dashboard Data: Last updated{' '}
                  <span style={{ 
                    color: dataFreshness === 'green' ? '#10b981' : '#ef4444',
                    fontWeight: '600'
                  }} suppressHydrationWarning>
                    {isMounted ? mostRecentUpdate : 'Loading...'}
                  </span>
                </p>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', textAlign: 'center', flexWrap: 'wrap' }}>
                <div style={{ minWidth: '70px' }}>
                    <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#111827', lineHeight: '1.2' }}>{totalApps}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '500', marginTop: '2px' }}>Total</div>
                </div>
                <div style={{ minWidth: '70px' }}>
                    <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#10b981', lineHeight: '1.2' }}>{activeAppsCount}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '500', marginTop: '2px' }}>Active</div>
                </div>
                <div style={{ minWidth: '70px' }}>
                    <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#3b82f6', lineHeight: '1.2' }}>{completedAppsCount}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '500', marginTop: '2px' }}>Checked</div>
                </div>
            </div>
        </div>
      </header>

      {/* Filters Section */}
      <section className="tag-filters-section" style={{ marginBottom: '1rem', background: 'white', padding: '1.25rem', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Status Filters */}
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111827', marginTop: '6px', minWidth: '85px' }}>Status:</span>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', flex: 1 }}>
              {statusFilters.map(filter => (
                <button
                  key={filter.id}
                  onClick={() => setFilterStatus(filter.value)}
                  style={{
                    padding: '6px 16px',
                    borderRadius: '20px',
                    border: `1px solid ${filterStatus === filter.value ? '#2563eb' : '#e5e7eb'}`,
                    background: filterStatus === filter.value ? '#2563eb' : 'white',
                    color: filterStatus === filter.value ? 'white' : '#4b5563',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: filterStatus === filter.value ? '600' : '500',
                    transition: 'all 0.15s ease',
                    boxShadow: filterStatus === filter.value ? '0 1px 2px 0 rgba(37, 99, 235, 0.3)' : '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
                  }}
                  onMouseEnter={(e) => {
                    if (filterStatus !== filter.value) {
                      e.currentTarget.style.borderColor = '#9ca3af';
                      e.currentTarget.style.background = '#f9fafb';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (filterStatus !== filter.value) {
                      e.currentTarget.style.borderColor = '#e5e7eb';
                      e.currentTarget.style.background = 'white';
                    }
                  }}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
          
          <div style={{ height: '1px', background: '#f3f4f6', width: '100%' }}></div>
          
          {/* Categories */}
          {categoryTags.length > 0 && (
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111827', marginTop: '6px', minWidth: '85px' }}>Categories:</span>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', flex: 1 }}>
              {categoryTags.map(tag => (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id, [])}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '6px',
                    border: `1px solid ${activeTags.includes(tag.id) ? '#10b981' : '#e5e7eb'}`,
                    background: activeTags.includes(tag.id) ? '#10b981' : 'white',
                    color: activeTags.includes(tag.id) ? 'white' : '#4b5563',
                    cursor: 'pointer',
                    fontSize: '0.8125rem',
                    fontWeight: activeTags.includes(tag.id) ? '600' : '500',
                    transition: 'all 0.15s ease',
                    boxShadow: activeTags.includes(tag.id) ? '0 1px 2px 0 rgba(16, 185, 129, 0.3)' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    if (!activeTags.includes(tag.id)) {
                      e.currentTarget.style.borderColor = '#9ca3af';
                      e.currentTarget.style.background = '#f9fafb';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!activeTags.includes(tag.id)) {
                      e.currentTarget.style.borderColor = '#e5e7eb';
                      e.currentTarget.style.background = 'white';
                    }
                  }}
                >
                  {tag.label}
                </button>
              ))}
              
              {activeTags.length > 0 && (
                <button
                  onClick={() => setActiveTags([])}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    background: 'white',
                    color: '#6b7280',
                    cursor: 'pointer',
                    fontSize: '0.8125rem',
                    fontWeight: '500',
                    transition: 'all 0.15s ease',
                    marginLeft: 'auto'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#9ca3af';
                    e.currentTarget.style.background = '#f9fafb';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#d1d5db';
                    e.currentTarget.style.background = 'white';
                  }}
                >
                  Clear All
                </button>
              )}
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="search-section" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap', background: 'white', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
        
        <div className="search-input-wrapper" style={{ display: 'flex', alignItems: 'center', flex: '1 1 auto', minWidth: '200px' }}>
            <input 
                type="text" 
                placeholder="Search by name, title, description..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ 
                  padding: '0.75rem 1rem', 
                  borderRadius: '8px', 
                  border: '1px solid #d1d5db', 
                  width: '100%', 
                  fontSize: '0.95rem',
                  outline: 'none',
                  transition: 'border-color 0.15s ease',
                  boxSizing: 'border-box',
                  backgroundColor: '#ffffff',
                  color: '#111827'
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
            />
        </div>

        <div style={{ fontSize: '0.875rem', color: '#374151', fontWeight: '500', whiteSpace: 'nowrap', marginLeft: 'auto' }}>
            {filterStatus !== 'All' || searchTerm || activeTags.length > 0 ? (
                <span>
                    <span style={{ fontWeight: '600', color: '#111827' }}>{filteredAndSortedApps.length}</span>
                    <span style={{ color: '#6b7280' }}> of </span>
                    <span style={{ fontWeight: '600', color: '#111827' }}>{totalApps}</span>
                    <span style={{ color: '#6b7280' }}> apps</span>
                </span>
            ) : (
                <span>
                    <span style={{ fontWeight: '600', color: '#111827' }}>{filteredAndSortedApps.length}</span>
                    <span style={{ color: '#6b7280' }}> apps</span>
                </span>
            )}
        </div>
      </section>

      {/* Desktop Table View */}
      <table className="desktop-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.95rem' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #333', background: '#fafafa' }}>
            <th 
                style={{ padding: '1rem', cursor: 'pointer', userSelect: 'none' }}
                onClick={() => handleSort('name')}
            >
                App {sortConfig.key === 'name' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
            </th>
            <th style={{ padding: '1rem', display: 'none' }}>Builder</th>
            <th 
                style={{ padding: '1rem', cursor: 'pointer', userSelect: 'none' }}
                onClick={() => handleSort('screenshots')}
            >
                Screenshots {sortConfig.key === 'screenshots' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
            </th>
            <th 
                style={{ padding: '1rem', cursor: 'pointer', userSelect: 'none' }}
                onClick={() => handleSort('status')}
            >
                Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
            </th>
            <th 
                style={{ padding: '1rem', cursor: 'pointer', userSelect: 'none' }}
                onClick={() => handleSort('lastUpdated')}
            >
                Github Last Updated {sortConfig.key === 'lastUpdated' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
            </th>
            <th 
                style={{ padding: '1rem', cursor: 'pointer', userSelect: 'none' }}
                onClick={() => handleSort('commits')}
            >
                Github Commits {sortConfig.key === 'commits' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
            </th>
            <th 
                style={{ padding: '1rem', cursor: 'pointer', userSelect: 'none' }}
                onClick={() => handleSort('lastChecked')}
            >
                Last Checked {sortConfig.key === 'lastChecked' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
            </th>
          </tr>
        </thead>
        <tbody>
          {filteredAndSortedApps.length === 0 ? (
            <tr><td colSpan={7} style={{ padding: '3rem', textAlign: 'center', fontSize: '1.2rem', color: '#666' }}>No apps found matching criteria.</td></tr>
          ) : (
            filteredAndSortedApps.map((appData, index) => {
              const { name, title, description, categories, screenshots, icon, lastUpdated, commit, status, commits, builder, prompt, prompts, rank } = appData;
              const assessment = assessApp(appData);
              const isDefault = status === 'Default';
              const isPending = status === 'Pending';
              const isInactive = status === 'Inactive';
              
              const rowBg = isDefault ? '#fff5f5' : (isPending ? '#fffff0' : (isInactive ? '#f3f4f6' : 'white'));

              return (
                <tr key={name} style={{ borderBottom: '1px solid #eee', background: rowBg }}>
                  <td style={{ padding: '1rem', verticalAlign: 'top', width: '350px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', position: 'relative' }}>
                        {FEATURED_APPS.includes(name) && (
                          <div title="Featured App" style={{ position: 'absolute', left: '-25px', fontSize: '1.2rem', cursor: 'help' }}>⭐</div>
                        )}
                        <div style={{ 
                            width: '50px', 
                            height: '50px', 
                            background: '#eee', 
                            borderRadius: '8px', 
                            overflow: 'hidden',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid #ddd',
                            flexShrink: 0
                        }}>
                            <Image 
                                src={icon || (screenshots.length > 0 ? `/apps/${name}/${screenshots[0]}` : '/placeholder.png')} 
                                alt="icon"
                                width={48}
                                height={48}
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                loading="lazy"
                                unoptimized={true}
                            />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <a 
                                href={`https://${name}.miniapp-factory.marketplace.openxai.network`} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                style={{ fontWeight: 'bold', fontSize: '1.1rem', color: '#0070f3', textDecoration: 'none' }}
                                onMouseOver={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'underline'}
                                onMouseOut={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'none'}
                            >
                                {title || name.replace(/-/g, ' ')} ↗
                            </a>
                            {description ? (
                                <p style={{ 
                                    margin: '4px 0 0 0', 
                                    fontSize: '0.85rem', 
                                    color: '#666', 
                                    display: '-webkit-box', 
                                    WebkitLineClamp: 2, 
                                    WebkitBoxOrient: 'vertical', 
                                    overflow: 'hidden',
                                    lineHeight: '1.4'
                                }}>
                                    {description}
                                </p>
                            ) : (
                                <span style={{ fontSize: '0.8rem', color: '#999', fontFamily: 'monospace', fontStyle: 'italic' }}>{name}</span>
                            )}
                            {categories && categories.length > 0 && (
                                <div style={{ 
                                    marginTop: '6px', 
                                    display: 'flex', 
                                    flexWrap: 'wrap', 
                                    gap: '4px' 
                                }}>
                                    {categories.map((category, idx) => (
                                        <span
                                            key={idx}
                                            style={{
                                                fontSize: '0.7rem',
                                                padding: '2px 8px',
                                                background: '#e8f4f8',
                                                color: '#2c5282',
                                                borderRadius: '12px',
                                                border: '1px solid #bee3f8',
                                                fontWeight: '500',
                                                whiteSpace: 'nowrap'
                                            }}
                                        >
                                            {category}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                  </td>
                  <td style={{ padding: '1rem', verticalAlign: 'top', fontSize: '0.9rem', fontFamily: 'monospace', color: '#666', display: 'none' }}>
                    {builder ? (
                      <span title={builder} style={{ fontSize: '0.8rem' }}>
                        {builder.length > 12 ? `${builder.substring(0, 6)}...${builder.substring(builder.length - 4)}` : builder}
                      </span>
                    ) : (
                      <span style={{ color: '#ccc' }}>-</span>
                    )}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      {screenshots.length === 0 ? <span style={{ color: '#999', fontStyle: 'italic', fontSize: '0.85rem' }}>No screenshots</span> : 
                      screenshots.slice(0, 3).map(shot => (
                        <div key={shot} style={{ width: '80px', cursor: 'pointer' }} onClick={() => openModal(`/apps/${name}/${shot}`, name, shot)}>
                          <SafeThumbnailImage
                            appName={name}
                            screenshotName={shot}
                            width={80}
                            height={45}
                            style={{ 
                              width: '100%', 
                              height: 'auto', 
                              borderRadius: '4px', 
                              border: '1px solid #ddd',
                              objectFit: 'cover',
                              aspectRatio: '16/9'
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: '1rem', verticalAlign: 'middle' }}>
                    <span style={{ 
                      background: isDefault ? '#c53030' : (isPending ? '#d69e2e' : (isInactive ? '#6b7280' : '#1e7e34')),
                      color: 'white',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontWeight: 'bold',
                      fontSize: '0.85rem',
                      whiteSpace: 'nowrap',
                      display: 'inline-block'
                    }}>
                      {status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', verticalAlign: 'middle', fontSize: '0.9rem', color: '#555' }} suppressHydrationWarning>
                    <span suppressHydrationWarning>{isMounted ? formatRelativeTime(appData.rawDate) : appData.lastUpdated}</span>
                    {commit && <div style={{ fontFamily: 'monospace', color: '#999', fontSize: '0.75rem', marginTop: '4px' }}>{commit}</div>}
                  </td>
                  <td style={{ padding: '1rem', verticalAlign: 'middle', fontSize: '0.9rem', color: '#555' }}>
                    {commits ? (
                      <div style={{ fontSize: '0.9rem', color: '#333', display: 'inline-block' }}>
                        <strong>{commits}</strong>
                        {(prompts || prompt) && (
                          <>
                            {' '}
                            <a
                              href="#"
                              onClick={(e) => {
                                e.preventDefault();
                                setClickedPrompt({ 
                                  app: name, 
                                  prompt: prompt, // Backward compatibility
                                  prompts: prompts || (prompt ? [{ type: 'Initial', text: prompt }] : null)
                                });
                              }}
                              style={{ 
                                color: '#0070f3', 
                                textDecoration: 'underline',
                                cursor: 'pointer',
                                fontSize: '0.9rem'
                              }}
                            >
                              prompts
                            </a>
                          </>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: '#999' }}>-</span>
                    )}
                  </td>
                  <td style={{ padding: '1rem', verticalAlign: 'middle', fontSize: '0.9rem', color: '#555' }} suppressHydrationWarning>
                    <span suppressHydrationWarning>{isMounted ? formatRelativeTime(appData.lastCheckedRaw) : appData.lastChecked}</span>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {/* Mobile Card View */}
      <div className="mobile-cards" style={{ display: 'none' }}>
        {filteredAndSortedApps.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', fontSize: '1.2rem', color: '#666' }}>No apps found matching criteria.</div>
        ) : (
          filteredAndSortedApps.map((appData, index) => {
            const { name, title, description, categories, screenshots, icon, lastUpdated, commit, status, commits, builder, prompt, prompts, rank } = appData;
            const assessment = assessApp(appData);
            const isDefault = status === 'Default';
            const isPending = status === 'Pending';
            const isInactive = status === 'Inactive';
            
            const cardBg = isDefault ? '#fff5f5' : (isPending ? '#fffff0' : (isInactive ? '#f3f4f6' : 'white'));

            return (
              <div key={name} className="mobile-card" style={{ 
                background: cardBg, 
                border: `1px solid ${isDefault ? '#feb2b2' : (isPending ? '#f6e05e' : (isInactive ? '#d1d5db' : '#e5e7eb'))}`,
                borderRadius: '12px',
                padding: '0',
                marginBottom: '1rem',
                marginLeft: 0,
                marginRight: 0,
                overflow: 'hidden',
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
              }}>
                {/* Main Content Row: 1/3 left (info) + 2/3 right (screenshot) */}
                <div style={{ display: 'flex', alignItems: 'stretch', height: '160px' }}>
                  {/* Left Side: Title, Description, Tags, Status (1/3) */}
                  <div style={{ 
                    flex: '0 0 33.333%', 
                    padding: '0.75rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    borderRight: '1px solid #e5e7eb',
                    overflow: 'hidden'
                  }}>
                    <div>
                      <a 
                        href={`https://${name}.miniapp-factory.marketplace.openxai.network`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ 
                          fontWeight: '600', 
                          fontSize: '0.875rem', 
                          color: '#3b82f6', 
                          textDecoration: 'none',
                          display: 'block',
                          marginBottom: '0.375rem',
                          lineHeight: '1.3'
                        }}
                        onMouseOver={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'underline'}
                        onMouseOut={(e) => (e.target as HTMLAnchorElement).style.textDecoration = 'none'}
                      >
                        {FEATURED_APPS.includes(name) && <span style={{ marginRight: '4px' }}>⭐</span>}
                        {title || name.replace(/-/g, ' ')} ↗
                      </a>
                    {description ? (
                      <p style={{ 
                          margin: '0 0 0.5rem 0', 
                          fontSize: '0.75rem', 
                          color: '#6b7280',
                          lineHeight: '1.4',
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                      }}>
                        {description}
                      </p>
                    ) : (
                        <div style={{ fontSize: '0.7rem', color: '#9ca3af', fontFamily: 'monospace', fontStyle: 'italic', marginBottom: '0.5rem' }}>{name}</div>
                      )}
                      {categories && categories.length > 0 && (
                        <div style={{ 
                          marginTop: '0.375rem',
                          display: 'flex', 
                          flexWrap: 'wrap', 
                          gap: '3px' 
                        }}>
                          {categories.slice(0, 2).map((category, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: '0.625rem',
                                padding: '2px 6px',
                                background: '#e8f4f8',
                                color: '#2c5282',
                                borderRadius: '4px',
                                border: '1px solid #bee3f8',
                                fontWeight: '500',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {category}
                            </span>
                          ))}
                          {categories.length > 2 && (
                            <span style={{
                              fontSize: '0.625rem',
                              color: '#6b7280',
                              padding: '2px 4px'
                            }}>
                              +{categories.length - 2}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    <div style={{ marginTop: 'auto', paddingTop: '0.5rem' }}>
                      <span style={{ 
                        background: isDefault ? '#ef4444' : (isPending ? '#f59e0b' : (isInactive ? '#6b7280' : '#10b981')),
                        color: 'white',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontWeight: '600',
                        fontSize: '0.7rem',
                        whiteSpace: 'nowrap',
                        display: 'inline-block'
                      }}>
                        {status.toUpperCase()}
                      </span>
                  </div>
                </div>

                  {/* Right Side: Screenshot (2/3) */}
                  <div style={{ 
                    flex: '0 0 66.666%',
                    position: 'relative',
                    background: '#f3f4f6',
                    cursor: screenshots.length > 0 ? 'pointer' : 'default',
                    height: '160px',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }} onClick={() => screenshots.length > 0 && openModal(`/apps/${name}/${screenshots[0]}`, name, screenshots[0])}>
                    {screenshots.length > 0 ? (
                          <SafeThumbnailImage
                            appName={name}
                        screenshotName={screenshots[0]}
                        width={300}
                        height={200}
                            style={{ 
                              width: '100%', 
                          height: '100%', 
                              objectFit: 'cover',
                          display: 'block'
                        }}
                      />
                    ) : (
                <div style={{ 
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#9ca3af',
                        fontSize: '0.75rem'
                      }}>
                        No screenshot
                    </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Prompt History Modal */}
      {clickedPrompt && (
        <>
          {/* Backdrop */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 1000
            }}
            onClick={() => setClickedPrompt(null)}
          />
          {/* Modal */}
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              left: '50%',
              top: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'white',
              border: '2px solid #0070f3',
              borderRadius: '12px',
              padding: '1.5rem',
              width: '90vw',
              maxWidth: '1200px',
              maxHeight: '85vh',
              overflow: 'auto',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              zIndex: 1001,
              fontSize: '0.9rem',
              lineHeight: '1.6',
              pointerEvents: 'auto'
            }}
          >
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '1rem', 
            paddingBottom: '0.75rem',
            borderBottom: '2px solid #eee'
          }}>
            <div style={{ fontWeight: 'bold', color: '#333', fontSize: '1.1rem' }}>
              Prompt History: {clickedPrompt.app}
            </div>
            <button
              onClick={() => setClickedPrompt(null)}
              style={{
                background: '#f0f0f0',
                border: '1px solid #ddd',
                borderRadius: '4px',
                padding: '4px 12px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 'bold'
              }}
            >
              ✕ Close
            </button>
          </div>
          
          {clickedPrompt.prompts && clickedPrompt.prompts.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {clickedPrompt.prompts.map((promptObj, index) => (
                <div 
                  key={index}
                  style={{
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    padding: '1rem',
                    background: index === 0 ? '#f9f9ff' : '#fafafa'
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    gap: '1rem',
                    marginBottom: '0.75rem'
                  }}>
                    <div style={{
                      minWidth: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      background: '#0070f3',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '1rem',
                      flexShrink: 0
                    }}>
                      {index + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        fontWeight: 'bold', 
                        color: '#0070f3', 
                        fontSize: '0.85rem',
                        marginBottom: '0.25rem'
                      }}>
                        {promptObj.type || 'Prompt'}
                      </div>
                      <div style={{ 
                        color: '#555', 
                        whiteSpace: 'pre-wrap', 
                        wordBreak: 'break-word',
                        fontSize: '0.9rem',
                        lineHeight: '1.7'
                      }}>
                        {promptObj.text}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : clickedPrompt.prompt ? (
            <div style={{ 
              color: '#555', 
              whiteSpace: 'pre-wrap', 
              wordBreak: 'break-word',
              fontSize: '0.9rem',
              lineHeight: '1.7',
              padding: '1rem',
              background: '#f9f9ff',
              borderRadius: '8px',
              border: '1px solid #e0e0e0'
            }}>
              {clickedPrompt.prompt}
            </div>
          ) : (
            <div style={{ color: '#999', fontStyle: 'italic' }}>
              No prompts found
            </div>
          )}
          </div>
        </>
      )}

      {/* Modal */}
      {selectedImage && (
        <div 
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0,0,0,0.9)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '2rem',
                backdropFilter: 'blur(5px)'
            }}
            onClick={closeModal}
        >
            <div 
                style={{ 
                    position: 'relative', 
                    maxWidth: '95vw', 
                    maxHeight: '95vh',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '1rem'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* App Title */}
                <div style={{
                    color: 'white',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    padding: '0.5rem 1rem',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    backdropFilter: 'blur(10px)'
                }}>
                    {selectedImage.appTitle || selectedImage.appName || 'Screenshot'}
                    {screenshotList.length > 0 && selectedImageIndex !== null && (
                        <span style={{ fontSize: '1rem', fontWeight: 'normal', opacity: 0.8, marginLeft: '0.5rem' }}>
                            ({selectedImageIndex + 1} / {screenshotList.length})
                        </span>
                    )}
                </div>

                {/* Image Container */}
                <div style={{ position: 'relative', maxWidth: '95vw', maxHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0' }}>
                    {/* Loading Spinner */}
                    {imageLoading && (
                        <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            zIndex: 10,
                            color: 'white',
                            fontSize: '2rem'
                        }}>
                            <div style={{
                                width: '50px',
                                height: '50px',
                                border: '4px solid rgba(255,255,255,0.3)',
                                borderTop: '4px solid white',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite'
                            }} />
                            <style>{`
                                @keyframes spin {
                                    0% { transform: rotate(0deg); }
                                    100% { transform: rotate(360deg); }
                                }
                            `}</style>
                        </div>
                    )}

                    {/* Desktop Navigation Buttons - Small arrows on sides */}
                    {screenshotList.length > 1 && selectedImageIndex !== null && (
                        <>
                            <button
                                className="desktop-nav-button desktop-nav-prev"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    navigateScreenshot('prev');
                                }}
                                style={{
                                    position: 'absolute',
                                    left: '10px',
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    background: 'white',
                                    border: '2px solid rgba(0,0,0,0.8)',
                                    color: 'black',
                                    fontSize: '2rem',
                                    cursor: 'pointer',
                                    width: '50px',
                                    height: '50px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transition: 'all 0.2s',
                                    zIndex: 5
                                }}
                                onMouseOver={(e) => {
                                    e.currentTarget.style.background = '#f0f0f0';
                                    e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
                                }}
                                onMouseOut={(e) => {
                                    e.currentTarget.style.background = 'white';
                                    e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
                                }}
                                aria-label="Previous screenshot"
                            >
                                ↑
                            </button>

                            <button
                                className="desktop-nav-button desktop-nav-next"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    navigateScreenshot('next');
                                }}
                                style={{
                                    position: 'absolute',
                                    right: '10px',
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    background: 'white',
                                    border: '2px solid rgba(0,0,0,0.8)',
                                    color: 'black',
                                    fontSize: '2rem',
                                    cursor: 'pointer',
                                    width: '50px',
                                    height: '50px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transition: 'all 0.2s',
                                    zIndex: 5
                                }}
                                onMouseOver={(e) => {
                                    e.currentTarget.style.background = '#f0f0f0';
                                    e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
                                }}
                                onMouseOut={(e) => {
                                    e.currentTarget.style.background = 'white';
                                    e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
                                }}
                                aria-label="Next screenshot"
                            >
                                ↓
                            </button>
                        </>
                    )}

                    {/* Image */}
                    <Image 
                        src={selectedImage.src || selectedImage} 
                        alt={`${selectedImage.appTitle || selectedImage.appName || 'Screenshot'}`}
                        width={1920}
                        height={1080}
                        style={{ 
                            maxWidth: '95vw', 
                            maxHeight: '80vh', 
                            objectFit: 'contain',
                            borderRadius: '8px',
                            boxShadow: '0 4px 30px rgba(0,0,0,0.5)',
                            opacity: imageLoading ? 0 : 1,
                            transition: 'opacity 0.3s'
                        }}
                        unoptimized
                        priority
                        onLoad={() => setImageLoading(false)}
                        onError={() => setImageLoading(false)}
                    />
                </div>

                {/* Close Button */}
                <button 
                    onClick={closeModal}
                    style={{
                        position: 'absolute',
                        top: '-50px',
                        right: 0,
                        background: 'rgba(255,255,255,0.2)',
                        border: 'none',
                        color: 'white',
                        fontSize: '2rem',
                        cursor: 'pointer',
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'background 0.2s'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.4)'}
                    onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                >
                    &times;
                </button>

                {/* Mobile Navigation Buttons - Triangle buttons */}
                {screenshotList.length > 1 && selectedImageIndex !== null && (
                    <div className="mobile-nav-buttons" style={{
                        position: 'absolute',
                        bottom: 'calc((100vh - 80vh - 2rem) / 2)',
                        left: 0,
                        right: 0,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        paddingLeft: 'calc(50% - 10vw)',
                        paddingRight: 'calc(50% - 10vw)',
                        zIndex: 5,
                        pointerEvents: 'none'
                    }}>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                navigateScreenshot('prev');
                            }}
                            style={{
                                width: 0,
                                height: 0,
                                borderTop: 'none',
                                borderBottom: '30px solid rgba(255,255,255,0.8)',
                                borderLeft: '20px solid transparent',
                                borderRight: '20px solid transparent',
                                background: 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                pointerEvents: 'auto',
                                touchAction: 'manipulation',
                                WebkitTapHighlightColor: 'transparent',
                                padding: 0,
                                margin: 0,
                                filter: 'drop-shadow(0 0 2px rgba(0,0,0,0.8)) drop-shadow(0 0 1px rgba(0,0,0,0.9))',
                                boxShadow: '0 0 0 2px rgba(0,0,0,0.8)'
                            }}
                            onTouchStart={(e) => {
                                e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,1)';
                                e.currentTarget.style.transform = 'scale(1.2)';
                            }}
                            onTouchEnd={(e) => {
                                e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,0.8)';
                                e.currentTarget.style.transform = 'scale(1)';
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,1)';
                                e.currentTarget.style.transform = 'scale(1.15)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,0.8)';
                                e.currentTarget.style.transform = 'scale(1)';
                            }}
                            aria-label="Previous screenshot"
                        />
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                navigateScreenshot('next');
                            }}
                            style={{
                                width: 0,
                                height: 0,
                                borderTop: '30px solid rgba(255,255,255,0.8)',
                                borderBottom: 'none',
                                borderLeft: '20px solid transparent',
                                borderRight: '20px solid transparent',
                                background: 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                pointerEvents: 'auto',
                                touchAction: 'manipulation',
                                WebkitTapHighlightColor: 'transparent',
                                padding: 0,
                                margin: 0,
                                filter: 'drop-shadow(0 0 2px rgba(0,0,0,0.8)) drop-shadow(0 0 1px rgba(0,0,0,0.9))',
                                boxShadow: '0 0 0 2px rgba(0,0,0,0.8)'
                            }}
                            onTouchStart={(e) => {
                                e.currentTarget.style.borderTopColor = 'rgba(255,255,255,1)';
                                e.currentTarget.style.transform = 'scale(1.2)';
                            }}
                            onTouchEnd={(e) => {
                                e.currentTarget.style.borderTopColor = 'rgba(255,255,255,0.8)';
                                e.currentTarget.style.transform = 'scale(1)';
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.borderTopColor = 'rgba(255,255,255,1)';
                                e.currentTarget.style.transform = 'scale(1.15)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.borderTopColor = 'rgba(255,255,255,0.8)';
                                e.currentTarget.style.transform = 'scale(1)';
                            }}
                            aria-label="Next screenshot"
                        />
                    </div>
                )}

                {/* Keyboard hint */}
                {screenshotList.length > 1 && (
                    <div className="keyboard-hint" style={{
                        color: 'rgba(255,255,255,0.6)',
                        fontSize: '0.85rem',
                        textAlign: 'center',
                        marginTop: '0.5rem'
                    }}>
                        Use ↑↓ arrow keys or click buttons to navigate
                    </div>
                )}
            </div>
        </div>
      )}
    </div>
    </>
  );
}
