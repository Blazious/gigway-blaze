import React from 'react';

const NetworkBackground = () => {
    return (
        <div className="network-background">
            <svg width="100%" height="100%" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid slice">
                <defs>
                    <linearGradient id="line-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.15" />
                        <stop offset="100%" stopColor="var(--secondary)" stopOpacity="0.1" />
                    </linearGradient>
                </defs>

                {/* Network Group 1 - Slow Motion */}
                <g className="network-group-1">
                    <circle cx="100" cy="200" r="3" fill="var(--primary)" opacity="0.4" />
                    <circle cx="300" cy="150" r="2" fill="var(--secondary)" opacity="0.3" />
                    <circle cx="250" cy="350" r="4" fill="var(--primary)" opacity="0.4" />
                    <circle cx="450" cy="400" r="2" fill="var(--secondary)" opacity="0.3" />
                    <circle cx="150" cy="500" r="3" fill="var(--primary)" opacity="0.35" />
                    <line x1="100" y1="200" x2="300" y2="150" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="300" y1="150" x2="250" y2="350" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="250" y1="350" x2="450" y2="400" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="100" y1="200" x2="250" y2="350" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="250" y1="350" x2="150" y2="500" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                </g>

                {/* Network Group 2 - Different position */}
                <g className="network-group-2">
                    <circle cx="800" cy="100" r="2" fill="var(--primary)" opacity="0.3" />
                    <circle cx="900" cy="300" r="3" fill="var(--secondary)" opacity="0.4" />
                    <circle cx="700" cy="400" r="2" fill="var(--primary)" opacity="0.3" />
                    <circle cx="850" cy="550" r="4" fill="var(--secondary)" opacity="0.4" />
                    <circle cx="950" cy="450" r="2" fill="var(--primary)" opacity="0.3" />
                    <line x1="800" y1="100" x2="900" y2="300" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="900" y1="300" x2="850" y2="550" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="700" y1="400" x2="850" y2="550" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="900" y1="300" x2="950" y2="450" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                </g>

                {/* Network Group 3 - Bottom left */}
                <g className="network-group-1" style={{ animationDelay: '-5s' }}>
                    <circle cx="150" cy="750" r="2" fill="var(--secondary)" opacity="0.3" />
                    <circle cx="350" cy="850" r="3" fill="var(--primary)" opacity="0.4" />
                    <circle cx="50" cy="900" r="2" fill="var(--secondary)" opacity="0.3" />
                    <circle cx="200" cy="950" r="4" fill="var(--primary)" opacity="0.35" />
                    <line x1="150" y1="750" x2="350" y2="850" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="150" y1="750" x2="50" y2="900" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                    <line x1="350" y1="850" x2="200" y2="950" stroke="url(#line-grad)" strokeWidth="1.5" strokeOpacity="0.3" />
                </g>

                {/* Subtle Dots pattern background */}
                <pattern id="dot-pattern" width="50" height="50" patternUnits="userSpaceOnUse">
                    <circle cx="2" cy="2" r="0.5" fill="var(--primary)" opacity="0.15" />
                </pattern>
                <rect width="100%" height="100%" fill="url(#dot-pattern)" />
            </svg>
        </div>
    );
};

export default NetworkBackground;
