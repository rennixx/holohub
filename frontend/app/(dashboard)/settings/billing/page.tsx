/**
 * Billing Settings Page
 *
 * Billing and subscription management.
 */
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAuthStore } from "@/lib/store";
import { organizationsApi } from "@/lib/api";
import {
  CreditCard,
  Package,
  CheckCircle2,
  ArrowRight,
  FileText,
  Download,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

// Mock plans data
const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    description: "For individuals and small teams",
    features: [
      "Up to 3 devices",
      "Up to 5 playlists",
      "Basic support",
      "Community forum access",
    ],
    cta: "Current Plan",
  },
  {
    id: "pro",
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For growing teams and businesses",
    features: [
      "Up to 50 devices",
      "Unlimited playlists",
      "Priority support",
      "Advanced analytics",
      "API access",
    ],
    cta: "Upgrade to Pro",
    popular: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "contact sales",
    description: "For large organizations",
    features: [
      "Unlimited everything",
      "Dedicated support",
      "Custom integrations",
      "SLA guarantee",
      "White-label options",
    ],
    cta: "Contact Sales",
  },
];

// Mock invoices data
const INVOICES = [
  {
    id: "inv-001",
    date: "2025-01-15",
    amount: "$29.00",
    status: "paid",
    description: "Pro Plan - January 2025",
  },
  {
    id: "inv-002",
    date: "2024-12-15",
    amount: "$29.00",
    status: "paid",
    description: "Pro Plan - December 2024",
  },
];

export default function BillingSettingsPage() {
  const { user } = useAuthStore();
  const { data: organization } = useQuery({
    queryKey: ["organization"],
    queryFn: () => organizationsApi.get(),
  });

  // Determine current plan based on tier
  const currentPlan = organization?.tier || "free";

  // Mock usage data
  const usage = {
    devices: 12,
    deviceLimit: currentPlan === "free" ? 3 : currentPlan === "pro" ? 50 : 9999,
    playlists: 8,
    playlistLimit: currentPlan === "free" ? 5 : 9999,
    storage: 2.4,
    storageLimit: currentPlan === "free" ? 10 : currentPlan === "pro" ? 100 : 1000,
  };

  const devicePercentage = (usage.devices / usage.deviceLimit) * 100;
  const storagePercentage = (usage.storage / usage.storageLimit) * 100;

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
            You are currently on the <span className="font-semibold text-white">{PLANS.find((p) => p.id === currentPlan)?.name}</span> plan
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Usage Stats */}
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-violet-300">Devices</span>
                <span className="text-white font-medium">
                  {usage.devices} / {usage.deviceLimit === 9999 ? "∞" : usage.deviceLimit}
                </span>
              </div>
              <Progress value={devicePercentage} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-violet-300">Playlists</span>
                <span className="text-white font-medium">
                  {usage.playlists} / {usage.playlistLimit === 9999 ? "∞" : usage.playlistLimit}
                </span>
              </div>
              <Progress value={(usage.playlists / usage.playlistLimit) * 100} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-violet-300">Storage</span>
                <span className="text-white font-medium">
                  {usage.storage}GB / {usage.storageLimit}GB
                </span>
              </div>
              <Progress value={storagePercentage} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Plans */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Available Plans</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {PLANS.map((plan) => (
            <Card
              key={plan.id}
              className={cn(
                "glass-holo transition-all",
                plan.popular && "ring-2 ring-violet-500 shadow-lg shadow-violet-500/20"
              )}
            >
              {plan.popular && (
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
                  variant={plan.id === currentPlan ? "secondary" : "holo-primary"}
                  className="w-full"
                  disabled={plan.id === currentPlan}
                  onClick={() => {
                    if (plan.id !== currentPlan) {
                      // Handle plan upgrade
                      if (plan.id === "enterprise") {
                        window.location.href = "mailto:sales@holohub.com?subject=Enterprise%20Plan%20Inquiry";
                      } else {
                        alert(`Upgrade to ${plan.name} plan - Payment integration coming soon!`);
                      }
                    }
                  }}
                >
                  {plan.cta}
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
            <Button variant="holo-secondary" size="sm">
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
            <Button variant="ghost" size="sm" className="text-violet-300">
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
          {INVOICES.length === 0 ? (
            <div className="text-center py-8 text-violet-400">
              No invoices yet
            </div>
          ) : (
            <div className="space-y-3">
              {INVOICES.map((invoice) => (
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
                    <span className="text-white font-medium">{invoice.amount}</span>
                    <Badge
                      variant="outline"
                      className={invoice.status === "paid" ? "text-green-500 border-green-500" : ""}
                    >
                      {invoice.status}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-violet-300 hover:text-white"
                      onClick={() => alert("Invoice download coming soon!")}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
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
