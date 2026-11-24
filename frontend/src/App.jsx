import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Assistant from './pages/Assistant';
import DocumentExplainer from './pages/DocumentExplainer';
import SchemeFinder from './pages/SchemeFinder';
import EligibilityChecker from './pages/EligibilityChecker';
import RightsExplorer from './pages/RightsExplorer';
import History from './pages/History';
import About from './pages/About';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="documents" element={<DocumentExplainer />} />
        <Route path="schemes" element={<SchemeFinder />} />
        <Route path="eligibility" element={<EligibilityChecker />} />
        <Route path="rights" element={<RightsExplorer />} />
        <Route path="history" element={<History />} />
        <Route path="about" element={<About />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
