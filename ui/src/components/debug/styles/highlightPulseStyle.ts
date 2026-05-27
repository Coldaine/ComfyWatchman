// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

// Add CSS for the highlight pulse effect
export const highlightPulseStyle = `
  @keyframes highlight-pulse {
    0% { 
      box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5);
    }
    70% { 
      box-shadow: 0 0 0 15px rgba(59, 130, 246, 0);
    }
    100% { 
      box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
    }
  }
  
  .highlight-pulse {
    animation: highlight-pulse 1.5s infinite;
    border: 2px solid #3b82f6;
  }

  @keyframes fade-in-out {
    0% { opacity: 0; transform: translateY(-20px); }
    10% { opacity: 1; transform: translateY(0); }
    90% { opacity: 1; transform: translateY(0); }
    100% { opacity: 0; transform: translateY(-20px); }
  }
  
  .animate-fade-in-out {
    animation: fade-in-out 3s forwards;
  }
`; 