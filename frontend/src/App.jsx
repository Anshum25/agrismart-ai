import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Diagnose from './pages/Diagnose'
import About from './pages/About'
import './index.css'

const pageVariants = {
  initial: { opacity: 0, y: 18 },
  enter:   { opacity: 1, y: 0, transition: { duration: .35, ease: [.4, 0, .2, 1] } },
  exit:    { opacity: 0, y: -10, transition: { duration: .2, ease: [.4, 0, .2, 1] } }
}

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={pageVariants}
        initial="initial"
        animate="enter"
        exit="exit"
        style={{ willChange: 'opacity, transform' }}
      >
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/diagnose" element={<Diagnose />} />
          <Route path="/about" element={<About />} />
        </Routes>
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
