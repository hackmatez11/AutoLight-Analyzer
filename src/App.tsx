import { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Results from './pages/Results';
import Reports from './pages/Reports';
import Profile from './pages/Profile';

function App() {
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedProjectId, setSelectedProjectId] = useState<string | undefined>();

  const handleNavigate = (page: string, projectId?: string) => {
    setCurrentPage(page);
    setSelectedProjectId(projectId);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'upload':
        return <Upload onNavigate={handleNavigate} />;
      case 'results':
        return <Results projectId={selectedProjectId} onNavigate={handleNavigate} />;
      case 'reports':
        return <Reports onNavigate={handleNavigate} />;
      case 'profile':
        return <Profile />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <Layout currentPage={currentPage} onNavigate={handleNavigate}>
      {renderPage()}
    </Layout>
  );
}

export default App;
