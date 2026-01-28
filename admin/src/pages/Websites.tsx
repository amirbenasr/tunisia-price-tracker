import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, ExternalLink, Play, Settings } from "lucide-react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import api, { Website } from "@/api/client";
import { formatRelativeTime } from "@/lib/utils";

interface WebsiteFormData {
  name: string;
  base_url: string;
  description: string;
  scraper_type: string;
  rate_limit_ms: number;
}

const initialFormData: WebsiteFormData = {
  name: "",
  base_url: "",
  description: "",
  scraper_type: "generic",
  rate_limit_ms: 1000,
};

export function Websites() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<WebsiteFormData>(initialFormData);

  const { data, isLoading } = useQuery({
    queryKey: ["websites"],
    queryFn: () => api.getWebsites(1, 100).then((res) => res.data),
  });

  const triggerScrape = useMutation({
    mutationFn: (websiteId: string) => api.triggerScrape(websiteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["websites"] });
    },
  });

  const createWebsite = useMutation({
    mutationFn: (data: WebsiteFormData) => api.createWebsite(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["websites"] });
      setIsDialogOpen(false);
      setFormData(initialFormData);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createWebsite.mutate(formData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "number" ? parseInt(value, 10) || 0 : value,
    }));
  };

  if (isLoading) {
    return (
      <div className="flex flex-col">
        <Header title="Websites" />
        <div className="p-6">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <Header title="Websites" />

      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <p className="text-muted-foreground">
            Manage competitor websites to track prices from
          </p>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Website
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={handleSubmit}>
                <DialogHeader>
                  <DialogTitle>Add New Website</DialogTitle>
                  <DialogDescription>
                    Add a new competitor website to track prices from.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      name="name"
                      placeholder="e.g., Tunisianet"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="base_url">Base URL</Label>
                    <Input
                      id="base_url"
                      name="base_url"
                      type="url"
                      placeholder="e.g., https://www.tunisianet.com.tn"
                      value={formData.base_url}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description (optional)</Label>
                    <Input
                      id="description"
                      name="description"
                      placeholder="Brief description of the website"
                      value={formData.description}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="scraper_type">Scraper Type</Label>
                    <Input
                      id="scraper_type"
                      name="scraper_type"
                      placeholder="e.g., generic, tunisianet, mytek"
                      value={formData.scraper_type}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="rate_limit_ms">Rate Limit (ms)</Label>
                    <Input
                      id="rate_limit_ms"
                      name="rate_limit_ms"
                      type="number"
                      min={100}
                      placeholder="1000"
                      value={formData.rate_limit_ms}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createWebsite.isPending}>
                    {createWebsite.isPending ? "Adding..." : "Add Website"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((website) => (
            <WebsiteCard
              key={website.id}
              website={website}
              onTriggerScrape={() => triggerScrape.mutate(website.id)}
              isScraping={triggerScrape.isPending}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface WebsiteCardProps {
  website: Website;
  onTriggerScrape: () => void;
  isScraping: boolean;
}

function WebsiteCard({
  website,
  onTriggerScrape,
  isScraping,
}: WebsiteCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{website.name}</CardTitle>
            <CardDescription className="mt-1">
              <a
                href={website.base_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 hover:underline"
              >
                {website.base_url}
                <ExternalLink className="h-3 w-3" />
              </a>
            </CardDescription>
          </div>
          <Badge variant={website.is_active ? "success" : "secondary"}>
            {website.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Products</span>
            <span className="font-medium">{website.total_products}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Last Scraped</span>
            <span className="font-medium">
              {website.last_scraped_at
                ? formatRelativeTime(website.last_scraped_at)
                : "Never"}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Rate Limit</span>
            <span className="font-medium">{website.rate_limit_ms}ms</span>
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={onTriggerScrape}
              disabled={isScraping || !website.is_active}
            >
              <Play className="mr-2 h-4 w-4" />
              Scrape
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to={`/scrapers/${website.id}`}>
                <Settings className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
