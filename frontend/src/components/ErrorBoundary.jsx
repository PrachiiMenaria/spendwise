import React from 'react';
import AlertBox from './AlertBox';
import { motion } from 'framer-motion';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="min-h-screen flex items-center justify-center bg-surface p-6"
        >
          <div className="max-w-lg w-full">
            <AlertBox 
              type="error" 
              title="Oops! Something went wrong." 
              message={this.state.error?.message || "There was a fatal component error."}
              className="mb-4 shadow-xl"
            />
            <button 
              className="btn-primary w-full shadow-md"
              onClick={() => window.location.reload()}
            >
              Refresh Page
            </button>
          </div>
        </motion.div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
