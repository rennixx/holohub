/**
 * Billing Settings Page
 *
 * Billing and subscription management.
 */
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAuthStore } from "@/lib/store";
import { billingApi } from "@/lib/api";
import type { PlanDetails, UsageStats, InvoiceItem } from "@/lib/api/billing";
import {
  CreditCard,
  Package,
  CheckCircle2,
  FileText,
  Download,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

export default function BillingSettingsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  // Fetch subscription info
  const { data: subscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ["billing", "subscription"],
    queryFn: () => billingApi.getSubscription(),
  });

  // Fetch usage stats
  const { data: usage, isLoading: usageLoading } = useQuery({
    queryKey: ["billing", "usage"],
    queryFn: () => billingApi.getUsage(),
  });

  // Fetch available plans
  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ["billing", "plans"],
    queryFn: () => billingApi.getPlans(),
  });

  // Fetch invoices
  const { data: invoices = [], isLoading: invoicesLoading } = useQuery({
    queryKey: ["billing", "invoices"],
    queryFn: () => billingApi.getInvoices(),
  });

  // Upgrade plan mutation
  const upgradeMutation = useMutation({
    mutationFn: (tier: string) => billingApi.upgradePlan(tier),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["billing"] });
      queryClient.invalidateQueries({ queryKey: ["organization"] });
      toast.success(data.message);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to upgrade plan";
      toast.error(message);
    },
  });

  const handleUpgrade = (tier: string) => {
    if (tier === "enterprise") {
      window.location.href = "mailto:sales@holohub.com?subject=Enterprise%20Plan%20Inquiry";
    } else {
      upgradeMutation.mutate(tier);
    }
  };

  const isLoading = subscriptionLoading || usageLoading || plansLoading || invoicesLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
      </div>
    );
  }

  const currentPlan = subscription?.plan;
  const currentTier = subscription?.tier || "free";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Billing & Plans
          </span>
        </h1>
        <p className="text-violet-300/70 mt-1">
          Manage your subscription and billing information
        </p>
      </div>

      {/* Current Plan */}
      <Card className="glass-holo">
        <CardHeader>
          <CardTitle className="text-white">Current Plan</CardTitle>
          <CardDescription className="text-violet-300/70">
            You are currently on the <span className="font-semibold text-white">{currentPlan?.name}</span> plan
            {subscription?.status && (
              <Badge variant="outline" className={cn(
                "ml-2",
                subscription.is_active ? "text-green-500 border-green-500" : "text-amber-500 border-amber-500"
              )}>
                {subscription.status}
              </Badge>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Usage Stats */}
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-violet-300">Devices</span>
                <span className="text-white font-medium">
                  {usage?.devices} / {usage?.device_limit === 9999 ? "∞" : usage?.device_limit}
                </span>
              </div>
              <Progress value={usage?.storage_percentage || 0} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-violet-300">Playlists</span>
                <span className="text-white font-medium">
                  {usage?.playlists} / {usage?.playlist_limit === 9999 ? "∞" : usage?.playlist_limit}
                </span>
              </div>
              <Progress value={(usage && usage.playlist_limit > 0 ? (usage.playlists / usage.playlist_limit) * 100 : 0)} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-violet-300">Storage</span>
                <span className="text-white font-medium">
                  {usage?.storage_gb}GB / {usage?.storage_limit_gb}GB
                </span>
              </div>
              <Progress value={usage?.storage_percentage || 0} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Plans */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Available Plans</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {plans?.map((plan) => (
            <Card
              key={plan.id}
              className={cn(
                "glass-holo transition-all",
                plan.is_current && "ring-2 ring-violet-500 shadow-lg shadow-violet-500/20",
                plan.id === "pro" && !plan.is_current && "hover:ring-2 hover:ring-violet-500/30"
              )}
            >
              {plan.id === "pro" && !plan.is_current && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-violet-600 to-cyan-500 text-white px-3 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}
              <CardHeader className="pt-6">
                <CardTitle className="text-white text-center">{plan.name}</CardTitle>
                <div className="text-center mt-2">
                  <span className="text-3xl font-bold text-white">{plan.price}</span>
                  <span className="text-violet-400 ml-1">{plan.period}</span>
                </div>
                <CardDescription className="text-center text-violet-300/70 mt-2">
                  {plan.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm text-violet-300">
                      <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button
                  variant={plan.is_current ? "secondary" : "holo-primary"}
                  className="w-full"
                  disabled={plan.is_current || upgradeMutation.isPending}
                  onClick={() => !plan.is_current && handleUpgrade(plan.id)}
                >
                  {upgradeMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : plan.is_current ? (
                    "Current Plan"
                  ) : plan.id === "enterprise" ? (
                    "Contact Sales"
                  ) : (
                    `Upgrade to ${plan.name}`
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Billing Information */}
      <Card className="glass-holo">
        <CardHeader>
          <CardTitle className="text-white">Billing Information</CardTitle>
          <CardDescription className="text-violet-300/70">
            Manage your payment methods and billing address
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-violet-950/30 border border-violet-500/10">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center">
                <CreditCard className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Payment Method</p>
                <p className="text-xs text-violet-400">No payment method on file</p>
              </div>
            </div>
            <Button variant="holo-secondary" size="sm" disabled>
              Add Payment Method
            </Button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-violet-950/30 border border-violet-500/10">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center">
                <Package className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Billing Email</p>
                <p className="text-xs text-violet-400">Invoices sent to {user?.email}</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" className="text-violet-300" disabled>
              Change
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Invoices */}
      <Card className="glass-holo">
        <CardHeader>
          <CardTitle className="text-white">Invoices</CardTitle>
          <CardDescription className="text-violet-300/70">
            View and download your billing history
          </CardDescription>
        </CardHeader>
        <CardContent>
          {invoices.length === 0 ? (
            <div className="text-center py-8 text-violet-400">
              No invoices yet
            </div>
          ) : (
            <div className="space-y-3">
              {invoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded bg-violet-600/20 flex items-center justify-center">
                      <FileText className="h-5 w-5 text-violet-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{invoice.description}</p>
                      <p className="text-xs text-violet-400">{invoice.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-white font-medium">
                      {invoice.currency === "USD" ? "$" : ""}{invoice.amount}
                    </span>
                    <Badge
                      variant="outline"
                      className={invoice.status === "paid" ? "text-green-500 border-green-500" : ""}
                    >
                      {invoice.status}
                    </Badge>
                    {invoice.invoice_pdf && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-violet-300 hover:text-white"
                        onClick={() => window.open(invoice.invoice_pdf, "_blank")}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
