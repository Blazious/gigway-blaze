import React from 'react';
import { BriefcaseBusiness } from 'lucide-react';
import '../styles/GigWayLoader.css';

const GigWayLoader = ({ label = 'Loading GigWay', compact = false }) => (
    <div className={`gigway-loader ${compact ? 'compact' : ''}`} role="status" aria-live="polite">
        <div className="gigway-loader-mark">
            <div className="gigway-loader-orbit"></div>
            <BriefcaseBusiness size={compact ? 22 : 30} />
        </div>
        <div className="gigway-loader-word">
            <span>Gig</span>Way
        </div>
        {label && <p>{label}</p>}
    </div>
);

export default GigWayLoader;
