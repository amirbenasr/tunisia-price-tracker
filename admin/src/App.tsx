import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Websites } from '@/pages/Websites'
import { Products } from '@/pages/Products'
import { Search } from '@/pages/Search'
import { Settings } from '@/pages/Settings'
import { PriceDrops } from '@/pages/PriceDrops'
import { Scrapers } from '@/pages/Scrapers'
import { ScraperConfig } from '@/pages/ScraperConfig'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="search" element={<Search />} />
        <Route path="websites" element={<Websites />} />
        <Route path="products" element={<Products />} />
        <Route path="price-drops" element={<PriceDrops />} />
        <Route path="scrapers" element={<Scrapers />} />
        <Route path="scrapers/:websiteId" element={<ScraperConfig />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
