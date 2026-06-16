import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { 
  Activity, MessageSquare, Lightbulb, PieChart as PieChartIcon, 
  BarChart2, Quote, PlayCircle, Folder, AlertCircle
} from 'lucide-react';
import './index.css';

interface Theme {
  name: string;
  description: string;
  quotes: string[];
  action_ideas: string[];
}

// Mocked Data for charts as original API doesn't provide it
const RATING_DATA = [
  { name: '5★', count: 265, color: '#10b981' },
  { name: '4★', count: 90, color: '#84cc16' },
  { name: '3★', count: 41, color: '#f59e0b' },
  { name: '2★', count: 37, color: '#f97316' },
  { name: '1★', count: 159, color: '#ef4444' },
];

const SOURCE_DATA = [
  { name: 'Play Store', value: 703, color: '#10b981' },
  { name: 'App Store', value: 104, color: '#3b82f6' },
];

function App() {
  const [weeks, setWeeks] = useState<{ iso_week: string }[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<string>('');
  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'themes' | 'trends' | 'report'>('overview');
  const [selectedThemeIndex, setSelectedThemeIndex] = useState<number>(0);

  useEffect(() => {
    fetch('http://localhost:8000/api/runs')
      .then((res) => res.json())
      .then((data) => {
        const sortedWeeks = (data.runs || []).sort((a: any, b: any) => 
          b.iso_week.localeCompare(a.iso_week)
        );
        setWeeks(sortedWeeks);
        if (sortedWeeks.length > 0) {
          setSelectedWeek(sortedWeeks[0].iso_week);
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to fetch runs:', err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedWeek) return;
    
    setLoading(true);
    fetch(`http://localhost:8000/api/themes/${selectedWeek}`)
      .then((res) => res.json())
      .then((data) => {
        setThemes(data.themes || []);
        setSelectedThemeIndex(0);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch themes:', err);
        setThemes([]);
        setLoading(false);
      });
  }, [selectedWeek]);

  const totalActionIdeas = themes.reduce((acc, t) => acc + t.action_ideas.length, 0);
  const totalQuotes = themes.reduce((acc, t) => acc + t.quotes.length, 0);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="logo-section">
          <Activity size={32} color="#ec4899" />
          <span className="logo-text">Groww Pulse</span>
        </div>
        
        <div className="header-controls">
          {weeks.length > 0 && (
            <select 
              className="styled-select"
              value={selectedWeek}
              onChange={(e) => setSelectedWeek(e.target.value)}
            >
              {weeks.map((w) => (
                <option key={w.iso_week} value={w.iso_week}>
                  {w.iso_week}
                </option>
              ))}
            </select>
          )}
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'themes', label: 'Themes' },
          { id: 'trends', label: 'Trends' },
          { id: 'report', label: 'Report' },
        ].map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id as any)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p style={{ color: 'var(--text-muted)' }}>Analyzing Play Store Insights...</p>
          </div>
        ) : themes.length === 0 ? (
          <div className="empty-state">
            <Folder />
            <h2>No Data Found</h2>
            <p>We couldn't find any themes for the selected week.</p>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="overview-grid animate-fade-in">
                {/* Metrics Row */}
                <div className="metrics-row">
                  <div className="glass-card metric-card">
                    <div className="metric-header">
                      <PieChartIcon size={16} color="var(--accent-primary)" />
                      <span>Analyzed Reviews</span>
                    </div>
                    <div className="metric-value">807</div>
                    <div className="metric-sub">Total reviews analyzed this week</div>
                  </div>

                  <div className="glass-card metric-card">
                    <div className="metric-header">
                      <Folder size={16} color="var(--accent-secondary)" />
                      <span>Core Themes</span>
                    </div>
                    <div className="metric-value">{themes.length}</div>
                    <div className="metric-sub">Key topics identified</div>
                  </div>

                  <div className="glass-card metric-card">
                    <div className="metric-header">
                      <MessageSquare size={16} color="var(--success)" />
                      <span>Verified Quotes</span>
                    </div>
                    <div className="metric-value">{totalQuotes}</div>
                    <div className="metric-sub">Direct user verbatims extracted</div>
                  </div>

                  <div className="glass-card metric-card">
                    <div className="metric-header">
                      <Lightbulb size={16} color="var(--warning)" />
                      <span>Action Ideas</span>
                    </div>
                    <div className="metric-value">{totalActionIdeas}</div>
                    <div className="metric-sub">AI-generated recommendations</div>
                  </div>
                </div>

                {/* Charts Row */}
                <div className="charts-row">
                  <div className="glass-card chart-card">
                    <h3 className="chart-title">Source Breakdown</h3>
                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={SOURCE_DATA}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={5}
                            dataKey="value"
                            stroke="none"
                          >
                            {SOURCE_DATA.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip 
                            contentStyle={{ background: 'var(--bg-panel)', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
                            itemStyle={{ color: '#fff' }}
                          />
                          <Legend verticalAlign="bottom" height={36} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="glass-card chart-card">
                    <h3 className="chart-title">Rating Distribution</h3>
                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={RATING_DATA} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                          <XAxis type="number" hide />
                          <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)' }} />
                          <Tooltip
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            contentStyle={{ background: 'var(--bg-panel)', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
                          />
                          <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={24}>
                            {RATING_DATA.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Themes Summary */}
                <div className="glass-card themes-summary">
                  <h3 className="themes-summary-title">Top Themes Summary</h3>
                  <div className="theme-summary-list">
                    {themes.slice(0, 3).map((theme, i) => (
                      <div key={i} className="theme-summary-item" onClick={() => { setActiveTab('themes'); setSelectedThemeIndex(i); }} style={{cursor: 'pointer'}}>
                        <div className="theme-rank">#{i + 1}</div>
                        <div className="theme-summary-content">
                          <h4>{theme.name}</h4>
                          <p>{theme.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'themes' && (
              <div className="themes-layout animate-fade-in">
                {/* Sidebar */}
                <div className="themes-sidebar glass-card">
                  {themes.map((theme, i) => (
                    <div 
                      key={i} 
                      className={`theme-list-item ${selectedThemeIndex === i ? 'active' : ''}`}
                      onClick={() => setSelectedThemeIndex(i)}
                    >
                      <div className="theme-list-title">{theme.name}</div>
                      <div className="theme-list-meta">
                        <span><MessageSquare size={14} /> {theme.quotes.length}</span>
                        <span><Lightbulb size={14} /> {theme.action_ideas.length}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Detail View */}
                <div className="glass-card theme-detail-panel">
                  {themes[selectedThemeIndex] && (
                    <>
                      <div className="detail-header">
                        <h2 className="detail-title">{themes[selectedThemeIndex].name}</h2>
                        <p className="detail-desc">{themes[selectedThemeIndex].description}</p>
                      </div>

                      <div className="detail-section">
                        <div className="detail-section-title">
                          <MessageSquare size={20} color="var(--accent-secondary)" />
                          Verified Quotes ({themes[selectedThemeIndex].quotes.length})
                        </div>
                        {themes[selectedThemeIndex].quotes.map((quote, i) => (
                          <div key={i} className="quote-box">"{quote}"</div>
                        ))}
                        {themes[selectedThemeIndex].quotes.length === 0 && (
                          <div style={{color: 'var(--text-muted)', fontStyle: 'italic'}}>No quotes available.</div>
                        )}
                      </div>

                      <div className="detail-section">
                        <div className="detail-section-title">
                          <Lightbulb size={20} color="var(--success)" />
                          AI Action Ideas ({themes[selectedThemeIndex].action_ideas.length})
                        </div>
                        {themes[selectedThemeIndex].action_ideas.map((idea, i) => (
                          <div key={i} className="action-idea-box">
                            <PlayCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
                            <div>{idea}</div>
                          </div>
                        ))}
                        {themes[selectedThemeIndex].action_ideas.length === 0 && (
                          <div style={{color: 'var(--text-muted)', fontStyle: 'italic'}}>No action ideas available.</div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {(activeTab === 'trends' || activeTab === 'report') && (
              <div className="glass-card empty-state animate-fade-in">
                <AlertCircle size={64} />
                <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} View</h2>
                <p>This module is currently under active development. Check back soon for deeper insights and automated reporting features.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
