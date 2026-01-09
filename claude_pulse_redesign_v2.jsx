import React, { useState } from 'react';

const ClaudePulseRedesign = () => {
  const [sessionPercent] = useState(77);
  const [sessionTimePercent] = useState(1); // 1% of 5-hour window elapsed
  const [weeklyUsage] = useState(20);
  const [weekElapsed] = useState(16);
  const [resetTime] = useState({ hours: 0, minutes: 57 });
  const [activeModel, setActiveModel] = useState('sonnet');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  
  const pacingRatio = weeklyUsage / weekElapsed;
  const isOverBudget = pacingRatio > 1;
  
  // Outer ring (usage) calculation
  const outerRadius = 72;
  const outerCircumference = 2 * Math.PI * outerRadius;
  const outerStrokeDashoffset = outerCircumference - (sessionPercent / 100) * outerCircumference;
  
  // Inner ring (time) calculation
  const innerRadius = 58;
  const innerCircumference = 2 * Math.PI * innerRadius;
  const innerStrokeDashoffset = innerCircumference - (sessionTimePercent / 100) * innerCircumference;
  
  return (
    <div style={{
      fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
      background: 'linear-gradient(145deg, #0a0a0f 0%, #12121a 50%, #0d0d14 100%)',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=JetBrains+Mono:wght@300;400;500&display=swap');
        
        @keyframes pulse {
          0%, 100% { opacity: 0.4; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.02); }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-4px); }
        }
        
        @keyframes arcDraw {
          from { stroke-dashoffset: 452; }
        }
        
        @keyframes arcDrawInner {
          from { stroke-dashoffset: 364; }
        }
        
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulseGlow {
          0%, 100% { filter: drop-shadow(0 0 6px rgba(0,180,255,0.4)); }
          50% { filter: drop-shadow(0 0 12px rgba(0,180,255,0.6)); }
        }
        
        .glass-card {
          backdrop-filter: blur(40px);
          -webkit-backdrop-filter: blur(40px);
        }
        
        .model-btn {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .model-btn:hover {
          transform: translateY(-1px);
        }
        
        .notification-toggle {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
      `}</style>
      
      <div className="glass-card" style={{
        width: '380px',
        background: 'linear-gradient(165deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
        borderRadius: '28px',
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: `
          0 4px 24px rgba(0,0,0,0.4),
          0 8px 48px rgba(0,0,0,0.3),
          inset 0 1px 0 rgba(255,255,255,0.05)
        `,
        overflow: 'hidden',
        position: 'relative',
      }}>
        {/* Ambient glow effect */}
        <div style={{
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: `radial-gradient(circle at 60% 30%, ${isOverBudget ? 'rgba(255,120,80,0.08)' : 'rgba(80,200,255,0.08)'} 0%, transparent 50%)`,
          pointerEvents: 'none',
          animation: 'pulse 4s ease-in-out infinite',
        }} />
        
        {/* Header with Logo */}
        <div style={{
          padding: '24px 28px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.04)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'relative',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            {/* Claude Pulse Logo - Speech bubble with heartbeat */}
            <div style={{
              width: '42px',
              height: '42px',
              position: 'relative',
            }}>
              <svg viewBox="0 0 100 100" width="42" height="42">
                {/* Speech bubble shape */}
                <defs>
                  <linearGradient id="bubbleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3a5a80" />
                    <stop offset="100%" stopColor="#2a4060" />
                  </linearGradient>
                  <linearGradient id="heartbeatGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#00b4ff" />
                    <stop offset="50%" stopColor="#ff8c42" />
                    <stop offset="100%" stopColor="#ff8c42" />
                  </linearGradient>
                  <filter id="glow">
                    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                {/* Speech bubble */}
                <path 
                  d="M50 10 C25 10 10 28 10 48 C10 68 25 82 45 82 L35 95 L50 82 C75 82 90 68 90 48 C90 28 75 10 50 10"
                  fill="url(#bubbleGradient)"
                  stroke="rgba(100,150,200,0.3)"
                  strokeWidth="1"
                />
                
                {/* Heartbeat line with C shape */}
                <path 
                  d="M20 48 L35 48 L40 30 L50 65 L60 48 L70 48"
                  fill="none"
                  stroke="url(#heartbeatGradient)"
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter="url(#glow)"
                />
                
                {/* Orange arc (bottom of C) */}
                <path
                  d="M65 55 A20 20 0 0 1 35 55"
                  fill="none"
                  stroke="#ff8c42"
                  strokeWidth="3"
                  strokeLinecap="round"
                  filter="url(#glow)"
                />
              </svg>
            </div>
            <div>
              <h1 style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '17px',
                fontWeight: '600',
                color: '#ffffff',
                margin: 0,
                letterSpacing: '-0.3px',
              }}>
                <span style={{ color: '#ffffff' }}>Claude</span>
                <span style={{ color: '#ff8c42', marginLeft: '6px' }}>Pulse</span>
              </h1>
              <p style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '11px',
                color: 'rgba(255,255,255,0.4)',
                margin: 0,
                fontWeight: '400',
                letterSpacing: '0.5px',
                textTransform: 'uppercase',
              }}>Usage Monitor</p>
            </div>
          </div>
          
          {/* Window controls */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', cursor: 'pointer' }} />
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', cursor: 'pointer' }} />
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', cursor: 'pointer' }} />
          </div>
        </div>
        
        {/* Model Toggle */}
        <div style={{
          padding: '16px 28px',
          display: 'flex',
          gap: '8px',
        }}>
          {['sonnet', 'opus', 'all'].map((model) => (
            <button
              key={model}
              className="model-btn"
              onClick={() => setActiveModel(model)}
              style={{
                flex: 1,
                padding: '10px 16px',
                borderRadius: '10px',
                border: 'none',
                background: activeModel === model 
                  ? 'linear-gradient(135deg, rgba(255,140,66,0.2) 0%, rgba(255,160,100,0.15) 100%)'
                  : 'rgba(255,255,255,0.03)',
                color: activeModel === model ? '#ff8c42' : 'rgba(255,255,255,0.4)',
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                textTransform: 'capitalize',
                boxShadow: activeModel === model 
                  ? '0 2px 8px rgba(255,140,66,0.15), inset 0 1px 0 rgba(255,255,255,0.05)'
                  : 'none',
              }}
            >
              {model === 'all' ? 'All Models' : model}
            </button>
          ))}
        </div>
        
        {/* Session Gauge - Dual Ring */}
        <div style={{
          padding: '24px 28px 32px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          animation: 'fadeSlideUp 0.5s ease-out',
        }}>
          <p style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '10px',
            color: 'rgba(255,255,255,0.35)',
            margin: '0 0 20px 0',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            fontWeight: '400',
          }}>Session Usage</p>
          
          <div style={{ position: 'relative', width: '180px', height: '180px' }}>
            {/* Background glow */}
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '140px',
              height: '140px',
              borderRadius: '50%',
              background: sessionPercent > 80 
                ? 'radial-gradient(circle, rgba(255,100,80,0.15) 0%, transparent 70%)'
                : 'radial-gradient(circle, rgba(255,140,66,0.1) 0%, transparent 70%)',
              filter: 'blur(20px)',
            }} />
            
            <svg width="180" height="180" style={{ transform: 'rotate(-90deg)' }}>
              <defs>
                <linearGradient id="usageGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ff8c42" />
                  <stop offset="50%" stopColor="#ffa060" />
                  <stop offset="100%" stopColor={sessionPercent > 80 ? '#FF6B6B' : '#ffb070'} />
                </linearGradient>
                <linearGradient id="timeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00b4ff" />
                  <stop offset="100%" stopColor="#0090dd" />
                </linearGradient>
              </defs>
              
              {/* Outer Track (Usage) */}
              <circle
                cx="90"
                cy="90"
                r={outerRadius}
                fill="none"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth="8"
                strokeLinecap="round"
              />
              {/* Outer Progress (Usage - Orange) */}
              <circle
                cx="90"
                cy="90"
                r={outerRadius}
                fill="none"
                stroke="url(#usageGradient)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={outerCircumference}
                strokeDashoffset={outerStrokeDashoffset}
                style={{
                  animation: 'arcDraw 1.2s ease-out',
                  filter: 'drop-shadow(0 0 8px rgba(255,140,66,0.5))',
                }}
              />
              
              {/* Inner Track (Time) */}
              <circle
                cx="90"
                cy="90"
                r={innerRadius}
                fill="none"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth="6"
                strokeLinecap="round"
              />
              {/* Inner Progress (Time - Blue) */}
              <circle
                cx="90"
                cy="90"
                r={innerRadius}
                fill="none"
                stroke="url(#timeGradient)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={innerCircumference}
                strokeDashoffset={innerStrokeDashoffset}
                style={{
                  animation: 'arcDrawInner 1.2s ease-out, pulseGlow 2s ease-in-out infinite',
                }}
              />
            </svg>
            
            {/* Center content */}
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
            }}>
              <div style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '42px',
                fontWeight: '300',
                color: '#ffffff',
                letterSpacing: '-2px',
                lineHeight: '1',
              }}>
                {sessionPercent}
                <span style={{ fontSize: '20px', color: 'rgba(255,255,255,0.4)', fontWeight: '400' }}>%</span>
              </div>
              <div style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '11px',
                color: 'rgba(255,255,255,0.35)',
                marginTop: '4px',
                fontWeight: '300',
              }}>
                Resets in {resetTime.hours}h {resetTime.minutes}m
              </div>
              <div style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '10px',
                color: 'rgba(0,180,255,0.6)',
                marginTop: '2px',
                fontWeight: '400',
              }}>
                {sessionTimePercent}% of session time
              </div>
            </div>
          </div>
          
          {/* Legend */}
          <div style={{
            display: 'flex',
            gap: '24px',
            marginTop: '16px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#ff8c42',
                boxShadow: '0 0 8px rgba(255,140,66,0.5)',
              }} />
              <span style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '12px',
                color: 'rgba(255,255,255,0.5)',
              }}>Usage</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#00b4ff',
                boxShadow: '0 0 8px rgba(0,180,255,0.5)',
              }} />
              <span style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '12px',
                color: 'rgba(255,255,255,0.5)',
              }}>Time</span>
            </div>
          </div>
        </div>
        
        {/* Weekly Pace Section */}
        <div style={{
          padding: '24px 28px',
          background: 'rgba(0,0,0,0.2)',
          margin: '0 16px 16px',
          borderRadius: '16px',
          animation: 'fadeSlideUp 0.6s ease-out',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}>
            <p style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '10px',
              color: 'rgba(255,255,255,0.35)',
              margin: 0,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              fontWeight: '400',
            }}>Weekly Pace</p>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '20px',
              background: isOverBudget 
                ? 'rgba(255,100,80,0.15)' 
                : 'rgba(80,200,150,0.15)',
            }}>
              <div style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: isOverBudget ? '#FF6B6B' : '#50C896',
                boxShadow: `0 0 8px ${isOverBudget ? 'rgba(255,107,107,0.5)' : 'rgba(80,200,150,0.5)'}`,
              }} />
              <span style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '11px',
                fontWeight: '500',
                color: isOverBudget ? '#FF6B6B' : '#50C896',
              }}>
                {isOverBudget ? 'Over Budget' : 'On Track'}
              </span>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div style={{ position: 'relative', marginBottom: '12px' }}>
            {/* Track */}
            <div style={{
              height: '8px',
              borderRadius: '4px',
              background: 'rgba(255,255,255,0.06)',
              overflow: 'hidden',
            }}>
              {/* Usage fill */}
              <div style={{
                height: '100%',
                width: `${weeklyUsage}%`,
                borderRadius: '4px',
                background: isOverBudget 
                  ? 'linear-gradient(90deg, #ff8c42 0%, #FF6B6B 100%)'
                  : 'linear-gradient(90deg, #50C896 0%, #6DD5B0 100%)',
                boxShadow: isOverBudget 
                  ? '0 0 12px rgba(255,107,107,0.4)'
                  : '0 0 12px rgba(80,200,150,0.4)',
                transition: 'width 0.8s ease-out',
              }} />
            </div>
            
            {/* Time marker */}
            <div style={{
              position: 'absolute',
              left: `${weekElapsed}%`,
              top: '-4px',
              transform: 'translateX(-50%)',
              animation: 'float 3s ease-in-out infinite',
            }}>
              <div style={{
                width: '2px',
                height: '16px',
                background: 'rgba(255,255,255,0.6)',
                borderRadius: '1px',
                boxShadow: '0 0 8px rgba(255,255,255,0.3)',
              }} />
              <div style={{
                width: '8px',
                height: '8px',
                background: '#ffffff',
                borderRadius: '50%',
                marginLeft: '-3px',
                marginTop: '-2px',
                boxShadow: '0 0 12px rgba(255,255,255,0.5)',
              }} />
            </div>
          </div>
          
          {/* Labels */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <span style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '20px',
                fontWeight: '500',
                color: '#ffffff',
              }}>{weeklyUsage}%</span>
              <span style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '11px',
                color: 'rgba(255,255,255,0.35)',
                marginLeft: '6px',
              }}>used</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: '11px',
                color: 'rgba(255,255,255,0.35)',
              }}>{weekElapsed}% of week elapsed</span>
            </div>
          </div>
        </div>
        
        {/* Notification Toggle */}
        <div style={{
          padding: '16px 28px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ opacity: 0.4 }}>
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span style={{
              fontFamily: "'DM Sans', sans-serif",
              fontSize: '13px',
              color: 'rgba(255,255,255,0.5)',
            }}>Limit Alerts</span>
          </div>
          
          <button
            className="notification-toggle"
            onClick={() => setNotificationsEnabled(!notificationsEnabled)}
            style={{
              width: '44px',
              height: '24px',
              borderRadius: '12px',
              border: 'none',
              background: notificationsEnabled 
                ? 'linear-gradient(135deg, #ff8c42 0%, #ffa060 100%)'
                : 'rgba(255,255,255,0.1)',
              cursor: 'pointer',
              position: 'relative',
              boxShadow: notificationsEnabled 
                ? '0 2px 8px rgba(255,140,66,0.3)'
                : 'none',
            }}
          >
            <div style={{
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              background: '#ffffff',
              position: 'absolute',
              top: '3px',
              left: notificationsEnabled ? '23px' : '3px',
              transition: 'left 0.2s ease-out',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ClaudePulseRedesign;
