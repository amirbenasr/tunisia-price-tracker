import { useState } from 'react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function Settings() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('api_key') || '')

  const handleSaveApiKey = () => {
    localStorage.setItem('api_key', apiKey)
    alert('API key saved!')
  }

  return (
    <div className="flex flex-col">
      <Header title="Settings" />

      <div className="p-6">
        <div className="max-w-2xl space-y-6">
          {/* API Key Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>API Key</CardTitle>
              <CardDescription>
                Configure your API key for authenticated requests
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <Input
                  type="password"
                  placeholder="Enter your API key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleSaveApiKey}>Save</Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Your API key is stored locally in your browser and used for
                admin operations.
              </p>
            </CardContent>
          </Card>

          {/* About */}
          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Version</dt>
                  <dd>0.1.0</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">API URL</dt>
                  <dd>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
