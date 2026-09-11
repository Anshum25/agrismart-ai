import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import Diagnose from './pages/Diagnose.jsx'
import About from './pages/About.jsx'

export default function App() {
  return (
    <>
      <Navbar />
      <main className="page-content">
        <Routes>
          <Route path="/"         element={<Home />} />
          <Route path="/diagnose" element={<Diagnose />} />
          <Route path="/about"    element={<About />} />
          <Route path="*"         element={<Home />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>
          AgriSmart AI &nbsp;·&nbsp; Built for{' '}
          <a href="https://sih.gov.in" target="_blank" rel="noreferrer">
            Smart India Hackathon 2026
          </a>
          &nbsp;·&nbsp; ResNet50 · 98.96% accuracy
        </p>
      </footer>
    </>
  )
}
