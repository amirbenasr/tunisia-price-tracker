import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Save,
  Play,
  RefreshCw,
  Plus,
  FileText,
  Globe,
  Square,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
import api, { SitemapConfig } from "@/api/client";
import { formatRelativeTime } from "@/lib/utils";

type ConfigType = "product_list" | "sitemap";

interface FormState {
  config_type: ConfigType;
  selectors: Record<string, string>;
  sitemap_config: SitemapConfig;
}

const DEFAULT_SELECTORS: Record<string, string> = {
  container: "",
  item: "",
  name: "",
  price: "",
  original_price: "",
  image: "",
  url: "",
  in_stock: "",
  wait_for_selector: "",
};

const DEFAULT_SITEMAP_SELECTORS: Record<string, string> = {
  price: "",
  original_price: "",
  name: "",
  description: "",
  brand: "",
  in_stock: "",
  wait_for_selector: "",
};

const DEFAULT_SITEMAP_CONFIG: SitemapConfig = {
  sitemap_url: "",
  child_sitemap_pattern: "",
  url_include_pattern: "/products/",
  url_exclude_pattern: "",
  use_lastmod: true,
};

export function ScraperConfig() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const queryClient = useQueryClient();

  const [editMode, setEditMode] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [formState, setFormState] = useState<FormState>({
    config_type: "product_list",
    selectors: DEFAULT_SELECTORS,
    sitemap_config: DEFAULT_SITEMAP_CONFIG,
  });

  const { data: website } = useQuery({
    queryKey: ["website", websiteId],
    queryFn: () => api.getWebsite(websiteId!).then((res) => res.data),
    enabled: !!websiteId,
  });

  const { data: configs, isLoading } = useQuery({
    queryKey: ["scraper-configs", websiteId],
    queryFn: () => api.getScraperConfigs(websiteId!).then((res) => res.data),
    enabled: !!websiteId,
  });

  const { data: logs } = useQuery({
    queryKey: ["scrape-logs", websiteId],
    queryFn: () => api.getScrapeLogs(websiteId!, 1, 10).then((res) => res.data),
    enabled: !!websiteId,
  });

  // Find active config (either product_list or sitemap)
  const activeConfig = configs?.find((c) => c.is_active);

  // Sync form state when active config loads
  useEffect(() => {
    if (activeConfig && !editMode) {
      // Merge with defaults to ensure new fields show up
      const defaultSelectors =
        activeConfig.config_type === "sitemap"
          ? DEFAULT_SITEMAP_SELECTORS
          : DEFAULT_SELECTORS;
      setFormState({
        config_type: activeConfig.config_type as ConfigType,
        selectors: { ...defaultSelectors, ...activeConfig.selectors },
        sitemap_config: activeConfig.sitemap_config || DEFAULT_SITEMAP_CONFIG,
      });
    }
  }, [activeConfig, editMode]);

  const updateConfig = useMutation({
    mutationFn: (data: Partial<FormState>) =>
      api.updateScraperConfig(websiteId!, activeConfig!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["scraper-configs", websiteId],
      });
      setEditMode(false);
    },
  });

  const createConfig = useMutation({
    mutationFn: (data: Partial<FormState> & { website_id: string }) =>
      api.createScraperConfig(websiteId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["scraper-configs", websiteId],
      });
      setIsCreateDialogOpen(false);
      setFormState({
        config_type: "product_list",
        selectors: DEFAULT_SELECTORS,
        sitemap_config: DEFAULT_SITEMAP_CONFIG,
      });
    },
  });

  const triggerScrape = useMutation({
    mutationFn: () => api.triggerScrape(websiteId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scrape-logs", websiteId] });
    },
  });

  const stopScrape = useMutation({
    mutationFn: () => api.stopScrape(websiteId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scrape-logs", websiteId] });
    },
  });

  // Check if there's a running scrape
  const hasRunningScrape = logs?.items.some(
    (log) => log.status === "running" || log.status === "queued",
  );

  const handleEditClick = () => {
    if (activeConfig) {
      // Merge with defaults to ensure new fields show up
      const defaultSelectors =
        activeConfig.config_type === "sitemap"
          ? DEFAULT_SITEMAP_SELECTORS
          : DEFAULT_SELECTORS;
      setFormState({
        config_type: activeConfig.config_type as ConfigType,
        selectors: { ...defaultSelectors, ...activeConfig.selectors },
        sitemap_config: activeConfig.sitemap_config || DEFAULT_SITEMAP_CONFIG,
      });
      setEditMode(true);
    }
  };

  const handleSave = () => {
    updateConfig.mutate({
      config_type: formState.config_type,
      selectors: formState.selectors,
      sitemap_config:
        formState.config_type === "sitemap"
          ? formState.sitemap_config
          : undefined,
    });
  };

  const handleCreate = () => {
    createConfig.mutate({
      website_id: websiteId!,
      config_type: formState.config_type,
      selectors: formState.selectors,
      sitemap_config:
        formState.config_type === "sitemap"
          ? formState.sitemap_config
          : undefined,
    });
  };

  const handleSelectorChange = (key: string, value: string) => {
    setFormState((prev) => ({
      ...prev,
      selectors: { ...prev.selectors, [key]: value },
    }));
  };

  const handleSitemapConfigChange = (
    key: keyof SitemapConfig,
    value: string | boolean,
  ) => {
    setFormState((prev) => ({
      ...prev,
      sitemap_config: { ...prev.sitemap_config, [key]: value },
    }));
  };

  const handleConfigTypeChange = (type: ConfigType) => {
    setFormState((prev) => ({
      ...prev,
      config_type: type,
      selectors:
        type === "sitemap" ? DEFAULT_SITEMAP_SELECTORS : DEFAULT_SELECTORS,
    }));
  };

  if (!websiteId) {
    return <div>Invalid website ID</div>;
  }

  const isSitemap = formState.config_type === "sitemap";
  // Merge with defaults to show new fields even for existing configs
  const defaultSelectorsForDisplay =
    activeConfig?.config_type === "sitemap"
      ? DEFAULT_SITEMAP_SELECTORS
      : DEFAULT_SELECTORS;
  const displaySelectors = editMode
    ? formState.selectors
    : { ...defaultSelectorsForDisplay, ...(activeConfig?.selectors || {}) };
  const displaySitemapConfig = editMode
    ? formState.sitemap_config
    : activeConfig?.sitemap_config || DEFAULT_SITEMAP_CONFIG;

  return (
    <div className="flex flex-col">
      <Header title={`Scraper Config: ${website?.name || "Loading..."}`} />

      <div className="p-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Configuration Card */}
          <div className="space-y-6">
            {/* Scraper Type Selection (only in edit/create mode) */}
            {(editMode || !activeConfig) && (
              <Card>
                <CardHeader>
                  <CardTitle>Scraper Type</CardTitle>
                  <CardDescription>
                    Choose how to discover products on this website
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      type="button"
                      onClick={() => handleConfigTypeChange("product_list")}
                      className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                        !isSitemap
                          ? "border-primary bg-primary/5"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <Globe className="h-8 w-8" />
                      <span className="font-medium">CSS Selectors</span>
                      <span className="text-xs text-muted-foreground text-center">
                        Navigate pages and extract with CSS
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleConfigTypeChange("sitemap")}
                      className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                        isSitemap
                          ? "border-primary bg-primary/5"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <FileText className="h-8 w-8" />
                      <span className="font-medium">Sitemap</span>
                      <span className="text-xs text-muted-foreground text-center">
                        Discover products via sitemap.xml
                      </span>
                    </button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Sitemap Configuration (only for sitemap type) */}
            {((editMode && isSitemap) ||
              (!editMode && activeConfig?.config_type === "sitemap")) && (
              <Card>
                <CardHeader>
                  <CardTitle>Sitemap Settings</CardTitle>
                  <CardDescription>
                    Configure how to parse the sitemap
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="sitemap_url">Sitemap URL</Label>
                    {editMode ? (
                      <Input
                        id="sitemap_url"
                        value={formState.sitemap_config.sitemap_url}
                        onChange={(e) =>
                          handleSitemapConfigChange(
                            "sitemap_url",
                            e.target.value,
                          )
                        }
                        placeholder="https://example.com/sitemap.xml"
                      />
                    ) : (
                      <code className="block rounded bg-gray-100 p-2 text-sm">
                        {displaySitemapConfig.sitemap_url || "Not set"}
                      </code>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="child_sitemap_pattern">
                      Child Sitemap Pattern
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Regex to filter child sitemaps (e.g., "sitemap_products"
                      for Shopify)
                    </p>
                    {editMode ? (
                      <Input
                        id="child_sitemap_pattern"
                        value={
                          formState.sitemap_config.child_sitemap_pattern || ""
                        }
                        onChange={(e) =>
                          handleSitemapConfigChange(
                            "child_sitemap_pattern",
                            e.target.value,
                          )
                        }
                        placeholder="sitemap_products"
                      />
                    ) : (
                      <code className="block rounded bg-gray-100 p-2 text-sm">
                        {displaySitemapConfig.child_sitemap_pattern || "None"}
                      </code>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="url_include_pattern">
                      URL Include Pattern
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Only scrape URLs matching this regex (e.g., "/products/")
                    </p>
                    {editMode ? (
                      <Input
                        id="url_include_pattern"
                        value={
                          formState.sitemap_config.url_include_pattern || ""
                        }
                        onChange={(e) =>
                          handleSitemapConfigChange(
                            "url_include_pattern",
                            e.target.value,
                          )
                        }
                        placeholder="/products/"
                      />
                    ) : (
                      <code className="block rounded bg-gray-100 p-2 text-sm">
                        {displaySitemapConfig.url_include_pattern || "None"}
                      </code>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="url_exclude_pattern">
                      URL Exclude Pattern
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Skip URLs matching this regex (e.g.,
                      "/collections|/pages")
                    </p>
                    {editMode ? (
                      <Input
                        id="url_exclude_pattern"
                        value={
                          formState.sitemap_config.url_exclude_pattern || ""
                        }
                        onChange={(e) =>
                          handleSitemapConfigChange(
                            "url_exclude_pattern",
                            e.target.value,
                          )
                        }
                        placeholder="/collections|/pages"
                      />
                    ) : (
                      <code className="block rounded bg-gray-100 p-2 text-sm">
                        {displaySitemapConfig.url_exclude_pattern || "None"}
                      </code>
                    )}
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    {editMode ? (
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formState.sitemap_config.use_lastmod ?? true}
                          onChange={(e) =>
                            handleSitemapConfigChange(
                              "use_lastmod",
                              e.target.checked,
                            )
                          }
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <span className="text-sm">
                          Use lastmod for incremental scraping
                        </span>
                      </label>
                    ) : (
                      <Badge
                        variant={
                          displaySitemapConfig.use_lastmod
                            ? "success"
                            : "secondary"
                        }
                      >
                        {displaySitemapConfig.use_lastmod
                          ? "Incremental scraping enabled"
                          : "Full scrape each time"}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* CSS Selectors */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>
                      {activeConfig?.config_type === "sitemap"
                        ? "Product Page Selectors"
                        : "CSS Selectors"}
                    </CardTitle>
                    <CardDescription>
                      {activeConfig?.config_type === "sitemap"
                        ? "Selectors to extract data from individual product pages"
                        : "Configure selectors for extracting product data"}
                    </CardDescription>
                  </div>
                  {!editMode && activeConfig ? (
                    <Button variant="outline" onClick={handleEditClick}>
                      Edit
                    </Button>
                  ) : editMode ? (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setEditMode(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSave}
                        disabled={updateConfig.isPending}
                      >
                        <Save className="mr-2 h-4 w-4" />
                        Save
                      </Button>
                    </div>
                  ) : null}
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p>Loading...</p>
                ) : activeConfig || editMode ? (
                  <div className="space-y-4">
                    {Object.entries(displaySelectors).map(([key, value]) => (
                      <div key={key}>
                        <label className="mb-1 block text-sm font-medium capitalize">
                          {key.replace(/_/g, " ")}
                        </label>
                        {key === "wait_for_selector" && (
                          <p className="text-xs text-muted-foreground mb-1">
                            Wait for this element instead of networkidle (e.g.,
                            use price selector for reliability)
                          </p>
                        )}
                        {editMode ? (
                          <Input
                            value={formState.selectors[key] || ""}
                            onChange={(e) =>
                              handleSelectorChange(key, e.target.value)
                            }
                            placeholder={
                              key === "wait_for_selector"
                                ? "Leave empty for default (networkidle)"
                                : `CSS selector for ${key}`
                            }
                          />
                        ) : (
                          <code className="block rounded bg-gray-100 p-2 text-sm">
                            {value || "(not set)"}
                          </code>
                        )}
                      </div>
                    ))}

                    {activeConfig && !editMode && (
                      <div className="flex items-center gap-4 pt-4 text-sm text-muted-foreground">
                        <span>Version: {activeConfig.version}</span>
                        <span>|</span>
                        <span>Type: {activeConfig.config_type}</span>
                        <span>|</span>
                        <span>
                          Updated: {formatRelativeTime(activeConfig.updated_at)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <p className="text-muted-foreground mb-4">
                      No configuration found. Create one to start scraping.
                    </p>
                    <Dialog
                      open={isCreateDialogOpen}
                      onOpenChange={setIsCreateDialogOpen}
                    >
                      <DialogTrigger asChild>
                        <Button>
                          <Plus className="mr-2 h-4 w-4" />
                          Create Configuration
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                        <DialogHeader>
                          <DialogTitle>
                            Create Scraper Configuration
                          </DialogTitle>
                          <DialogDescription>
                            Configure how to scrape products from this website
                          </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-6 py-4">
                          {/* Type Selection */}
                          <div className="grid grid-cols-2 gap-4">
                            <button
                              type="button"
                              onClick={() =>
                                handleConfigTypeChange("product_list")
                              }
                              className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                                !isSitemap
                                  ? "border-primary bg-primary/5"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                            >
                              <Globe className="h-6 w-6" />
                              <span className="font-medium">CSS Selectors</span>
                              <span className="text-xs text-muted-foreground">
                                Page-based scraping
                              </span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleConfigTypeChange("sitemap")}
                              className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                                isSitemap
                                  ? "border-primary bg-primary/5"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                            >
                              <FileText className="h-6 w-6" />
                              <span className="font-medium">Sitemap</span>
                              <span className="text-xs text-muted-foreground">
                                Sitemap-based scraping
                              </span>
                            </button>
                          </div>

                          {/* Sitemap Config */}
                          {isSitemap && (
                            <div className="space-y-4 rounded-lg border p-4">
                              <h4 className="font-medium">Sitemap Settings</h4>
                              <div className="space-y-2">
                                <Label>Sitemap URL</Label>
                                <Input
                                  value={formState.sitemap_config.sitemap_url}
                                  onChange={(e) =>
                                    handleSitemapConfigChange(
                                      "sitemap_url",
                                      e.target.value,
                                    )
                                  }
                                  placeholder="https://example.com/sitemap.xml"
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Child Sitemap Pattern</Label>
                                <Input
                                  value={
                                    formState.sitemap_config
                                      .child_sitemap_pattern || ""
                                  }
                                  onChange={(e) =>
                                    handleSitemapConfigChange(
                                      "child_sitemap_pattern",
                                      e.target.value,
                                    )
                                  }
                                  placeholder="sitemap_products"
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>URL Include Pattern</Label>
                                <Input
                                  value={
                                    formState.sitemap_config
                                      .url_include_pattern || ""
                                  }
                                  onChange={(e) =>
                                    handleSitemapConfigChange(
                                      "url_include_pattern",
                                      e.target.value,
                                    )
                                  }
                                  placeholder="/products/"
                                />
                              </div>
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={
                                    formState.sitemap_config.use_lastmod ?? true
                                  }
                                  onChange={(e) =>
                                    handleSitemapConfigChange(
                                      "use_lastmod",
                                      e.target.checked,
                                    )
                                  }
                                  className="h-4 w-4"
                                />
                                <span className="text-sm">
                                  Enable incremental scraping
                                </span>
                              </label>
                            </div>
                          )}

                          {/* Selectors */}
                          <div className="space-y-4 rounded-lg border p-4">
                            <h4 className="font-medium">
                              {isSitemap
                                ? "Product Page Selectors"
                                : "CSS Selectors"}
                            </h4>
                            {Object.keys(formState.selectors).map((key) => (
                              <div key={key} className="space-y-1">
                                <Label className="capitalize">
                                  {key.replace(/_/g, " ")}
                                </Label>
                                {key === "wait_for_selector" && (
                                  <p className="text-xs text-muted-foreground">
                                    Wait for this element instead of networkidle
                                    (e.g., use price selector)
                                  </p>
                                )}
                                <Input
                                  value={formState.selectors[key] || ""}
                                  onChange={(e) =>
                                    handleSelectorChange(key, e.target.value)
                                  }
                                  placeholder={
                                    key === "wait_for_selector"
                                      ? "Leave empty for default"
                                      : `CSS selector for ${key}`
                                  }
                                />
                              </div>
                            ))}
                          </div>
                        </div>

                        <DialogFooter>
                          <Button
                            variant="outline"
                            onClick={() => setIsCreateDialogOpen(false)}
                          >
                            Cancel
                          </Button>
                          <Button
                            onClick={handleCreate}
                            disabled={createConfig.isPending}
                          >
                            {createConfig.isPending
                              ? "Creating..."
                              : "Create Configuration"}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Scrape Controls & Logs */}
          <div className="space-y-6">
            {/* Controls */}
            <Card>
              <CardHeader>
                <CardTitle>Scrape Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    onClick={() => triggerScrape.mutate()}
                    disabled={
                      triggerScrape.isPending ||
                      !website?.is_active ||
                      !activeConfig ||
                      hasRunningScrape
                    }
                  >
                    <Play className="mr-2 h-4 w-4" />
                    {triggerScrape.isPending ? "Starting..." : "Run Scrape Now"}
                  </Button>
                  {hasRunningScrape && (
                    <Button
                      variant="destructive"
                      onClick={() => stopScrape.mutate()}
                      disabled={stopScrape.isPending}
                    >
                      <Square className="mr-2 h-4 w-4" />
                      {stopScrape.isPending ? "Stopping..." : "Stop"}
                    </Button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Status</span>
                    <div className="mt-1">
                      <Badge
                        variant={website?.is_active ? "success" : "secondary"}
                      >
                        {website?.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Rate Limit</span>
                    <div className="mt-1 font-medium">
                      {website?.rate_limit_ms || 1000}ms
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Scraper Type</span>
                    <div className="mt-1">
                      <Badge variant="outline">
                        {activeConfig?.config_type === "sitemap"
                          ? "Sitemap"
                          : "CSS-based"}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Config</span>
                    <div className="mt-1">
                      <Badge variant={activeConfig ? "success" : "destructive"}>
                        {activeConfig ? "Configured" : "Not configured"}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Logs */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Recent Scrapes
                </CardTitle>
              </CardHeader>
              <CardContent>
                {logs?.items.length ? (
                  <div className="space-y-3">
                    {logs.items.map((log) => (
                      <div
                        key={log.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                log.status === "success"
                                  ? "success"
                                  : log.status === "failed"
                                    ? "destructive"
                                    : "secondary"
                              }
                            >
                              {log.status}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              {formatRelativeTime(log.started_at)}
                            </span>
                          </div>
                          <p className="mt-1 text-sm">
                            {log.products_found} found, {log.products_created}{" "}
                            created, {log.products_updated} updated
                          </p>
                        </div>
                        <div className="text-right text-sm text-muted-foreground">
                          {log.pages_scraped} pages
                          {log.duration_seconds && (
                            <div>{log.duration_seconds.toFixed(1)}s</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No scrape logs yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
