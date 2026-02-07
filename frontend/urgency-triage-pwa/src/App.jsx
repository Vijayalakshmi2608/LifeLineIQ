import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import SymptomInput from './pages/SymptomInput'
import TriageResults from './pages/TriageResults'
import HealthTimeline from './pages/HealthTimeline'
import CommunityInsights from './pages/CommunityInsights'
import OfflineReady from './pages/OfflineReady'
import Settings from './pages/Settings'
import NearestFacilities from './components/NearestFacilities'
import FollowUpResponse from './pages/FollowUpResponse'
import VisualCheck from './pages/VisualCheck'
import VisualResults from './pages/VisualResults'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <Home />
            </Layout>
          }
        />
        <Route
          path="/symptom"
          element={
            <Layout>
              <SymptomInput />
            </Layout>
          }
        />
        <Route
          path="/results"
          element={
            <Layout>
              <TriageResults />
            </Layout>
          }
        />
        <Route
          path="/timeline"
          element={
            <Layout>
              <HealthTimeline />
            </Layout>
          }
        />
        <Route
          path="/insights"
          element={
            <Layout>
              <CommunityInsights />
            </Layout>
          }
        />
        <Route
          path="/settings"
          element={
            <Layout>
              <Settings />
            </Layout>
          }
        />
        <Route
          path="/offline"
          element={
            <Layout>
              <OfflineReady />
            </Layout>
          }
        />
        <Route
          path="/facilities"
          element={
            <Layout>
              <NearestFacilities />
            </Layout>
          }
        />
        <Route
          path="/followup/:token"
          element={
            <Layout>
              <FollowUpResponse />
            </Layout>
          }
        />
        <Route
          path="/visual-check"
          element={
            <Layout>
              <VisualCheck />
            </Layout>
          }
        />
        <Route
          path="/visual-results"
          element={
            <Layout>
              <VisualResults />
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
