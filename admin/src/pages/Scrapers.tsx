import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Bot, Settings, CheckCircle, XCircle } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import api from '@/api/client'
import { formatRelativeTime } from '@/lib/utils'

export function Scrapers() {
  const { data: websites, isLoading } = useQuery({
    queryKey: ['websites'],
    queryFn: () => api.getWebsites(1, 100).then((res) => res.data),
  })

  return (
    <div className="flex flex-col">
      <Header title="Scrapers" />

      <div className="p-6">
        <div className="mb-6">
          <p className="text-muted-foreground">
            Manage scraper configurations for each website
          </p>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="space-y-4">
            {websites?.items.map((website) => (
              <Card key={website.id}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gray-100">
                      <Bot className="h-6 w-6 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-medium">{website.name}</h3>
                      <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
                        <span>{website.total_products} products</span>
                        <span>|</span>
                        <span>
                          Last run:{' '}
                          {website.last_scraped_at
                            ? formatRelativeTime(website.last_scraped_at)
                            : 'Never'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      {website.is_active ? (
                        <Badge variant="success" className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" />
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="flex items-center gap-1">
                          <XCircle className="h-3 w-3" />
                          Inactive
                        </Badge>
                      )}
                    </div>

                    <Button variant="outline" asChild>
                      <Link to={`/scrapers/${website.id}`}>
                        <Settings className="mr-2 h-4 w-4" />
                        Configure
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Help Card */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">How Scrapers Work</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            <ul className="list-inside list-disc space-y-2">
              <li>
                <strong>Config-driven scrapers</strong> use CSS selectors to extract product data.
                You can configure these without writing any code.
              </li>
              <li>
                <strong>Custom scrapers</strong> are Python classes for complex websites that
                require special handling (anti-bot bypass, login, etc.).
              </li>
              <li>
                Each website has a <strong>rate limit</strong> to avoid overloading the target
                server. Default is 1000ms between requests.
              </li>
              <li>
                Scrapers run automatically on a schedule (daily by default) or can be
                triggered manually.
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
