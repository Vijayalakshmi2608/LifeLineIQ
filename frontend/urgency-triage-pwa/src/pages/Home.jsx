import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  HeartPulse,
  Stethoscope,
  ClipboardList,
  ScanEye,
  CloudOff,
  Sparkles,
  ShieldCheck,
} from 'lucide-react'
import { usePwaInstall } from '../hooks/usePwaInstall'
import '../styles/home.css'

const container = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { staggerChildren: 0.12, duration: 0.5, ease: 'easeOut' },
  },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45 } },
}

const featureCards = [
  {
    title: 'Adaptive AI Questioning',
    description: 'Smart follow-ups adjust to your symptoms in real time.',
    icon: Sparkles,
  },
  {
    title: 'Health History Tracking',
    description: 'Track trends over time for better long-term insight.',
    icon: ClipboardList,
  },
  {
    title: 'Visual Symptom Analysis',
    description: 'Upload images to help assess visible symptoms.',
    icon: ScanEye,
  },
  {
    title: 'Offline-First with Smart Sync',
    description: 'Works without internet and syncs when you’re back online.',
    icon: CloudOff,
  },
]

const timelineSteps = [
  {
    title: 'Describe your symptoms',
    description: 'Share how you feel with simple, guided prompts.',
  },
  {
    title: 'Get AI guidance',
    description: 'Receive careful, clinically aligned next steps.',
  },
  {
    title: 'Know exactly what to do',
    description: 'Move forward with confidence and clarity.',
  },
]

const Home = () => {
  const { canInstall, promptInstall, dismissInstall } = usePwaInstall()
  const location = useLocation()
  const navigate = useNavigate()

  const handleInstall = async () => {
    await promptInstall()
  }

  useEffect(() => {
    if (location.hash === '#start') {
      const target = document.getElementById('start-check')
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }, [location.hash])

  const handleBeginNow = () => {
    if (location.pathname !== '/') {
      navigate('/#start')
      return
    }
    const target = document.getElementById('start-check')
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  return (
    <div className="home-page">
      <motion.section
        className="home-hero"
        initial="hidden"
        animate="visible"
        variants={container}
      >
        <div className="hero-content">
          <motion.div className="hero-eyebrow" variants={item}>
            <HeartPulse size={18} />
            <span>LifeLineIQ</span>
          </motion.div>

          <motion.h1 className="hero-title" variants={item}>
            Get the Right Care, Right Away
          </motion.h1>
          <motion.p className="hero-subtitle" variants={item}>
            A calm, AI-powered health assistant that guides you on what to do
            next.
          </motion.p>

          <motion.div className="hero-actions" variants={item} id="start-check">
            <button
              className="btn btn-primary"
              type="button"
              onClick={() => navigate('/symptom')}
            >
              Start My Health Check
            </button>
            <button
              className="btn btn-outline"
              type="button"
              onClick={() => navigate('/visual-check')}
            >
              Visual Symptom Checker
            </button>
            <button className="btn btn-outline" type="button">
              How It Works
            </button>
          </motion.div>


          <motion.div className="trust-badge" variants={item}>
            <ShieldCheck size={18} />
            <span>Clinically aligned · Works offline · Privacy-first</span>
          </motion.div>

          {canInstall && (
            <motion.div className="install-banner" variants={item}>
              <div>
                <strong>Install LifeLineIQ</strong>
                <p>
                  Add to your home screen for offline access and faster check-ins.
                </p>
              </div>
              <div className="install-actions">
                <button className="btn btn-primary" onClick={handleInstall}>
                  Install App
                </button>
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={dismissInstall}
                >
                  Not now
                </button>
              </div>
            </motion.div>
          )}
        </div>

        <motion.div className="hero-visual" variants={item}>
          <div className="hero-card">
            <Stethoscope size={28} />
            <div>
              <p className="hero-card-title">Clinically Aligned</p>
              <p className="hero-card-subtitle">
                Guidance grounded in medical best practices.
              </p>
            </div>
          </div>
        </motion.div>
      </motion.section>

      <section className="feature-section container">
        <div className="section-heading">
          <h2>Designed to Keep You Safe and Informed</h2>
          <p>
            LifeLineIQ combines modern AI with clinically aligned guidance so you
            can move forward with confidence.
          </p>
        </div>
        <div className="feature-grid">
          {featureCards.map((feature) => {
            const Icon = feature.icon
            return (
              <motion.div
                key={feature.title}
                className="feature-card"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={item}
              >
                <div className="feature-icon">
                  <Icon size={22} />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </motion.div>
            )
          })}
        </div>
      </section>

      <section className="timeline-section container">
        <div className="section-heading">
          <h2>A Simple 3-Step Flow</h2>
          <p>Get clarity in minutes with a focused, guided check-in.</p>
        </div>
        <div className="timeline">
          {timelineSteps.map((step, index) => (
            <motion.div
              key={step.title}
              className="timeline-step"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={item}
            >
              <div className="timeline-number">{index + 1}</div>
              <div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="why-section container">
        <div className="section-heading">
          <h2>Why LifeLineIQ?</h2>
          <p>Designed for everyone, everywhere, with calm and clarity.</p>
        </div>
        <ul className="why-list">
          <li>Built for all ages</li>
          <li>Works in low-internet areas</li>
          <li>Simple language</li>
          <li>No diagnosis, only safe guidance</li>
        </ul>
      </section>

      <section className="cta-section container">
        <div className="cta-card">
          <div>
            <h2>Start your health check in under 3 minutes.</h2>
            <p>Fast, private, and designed for peace of mind.</p>
          </div>
          <button className="btn btn-primary" type="button" onClick={handleBeginNow}>
            Begin Now
          </button>
        </div>
      </section>
    </div>
  )
}

export default Home
