import React, { createContext, useContext, useEffect, useState } from 'react';

interface CompactModeContextType {
  isCompact: boolean;
  setIsCompact: (compact: boolean) => void;
}

const CompactModeContext = createContext<CompactModeContextType | undefined>(undefined);

export const CompactModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isCompact, setIsCompact] = useState(() => {
    const saved = localStorage.getItem('compactMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('compactMode', JSON.stringify(isCompact));
    // Apply class to document root for CSS to use
    if (isCompact) {
      document.documentElement.classList.add('compact-mode');
    } else {
      document.documentElement.classList.remove('compact-mode');
    }
  }, [isCompact]);

  return (
    <CompactModeContext.Provider value={{ isCompact, setIsCompact }}>
      {children}
    </CompactModeContext.Provider>
  );
};

export const useCompactMode = () => {
  const context = useContext(CompactModeContext);
  if (!context) {
    throw new Error('useCompactMode must be used within CompactModeProvider');
  }
  return context;
};
