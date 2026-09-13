import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Diagnose from './pages/Diagnose'
import About from './pages/About'
import './index.css'

// Leaflet is only needed on the map page.
const Outbreaks = lazy(() => import('./pages/Outbreaks'))

const pageVariants = {
  initial: { opacity: 0, y: 18 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] } },
}

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <motion.div key={location.pathname} variants={pageVariants} initial="initial" animate="enter" exit="exit">
        <Suspense fallback={<div className="page-loading"><Loader2 className="spin" /></div>}>
          <Routes location={location}>
            <Route path="/" element={<Home />} />
            <Route path="/diagnose" element={<Diagnose />} />
            <Route path="/outbreaks" element={<Outbreaks />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </Suspense>
      </motion.div>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <>
      <Navbar />
      <div className="page-wrapper">
        <AnimatedRoutes />
      </div>
    </>
  )
}
