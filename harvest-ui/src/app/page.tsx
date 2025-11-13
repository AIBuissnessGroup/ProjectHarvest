"use client"

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { ArrowRight, BarChart3, Zap, Sparkles, LogIn, User, Lock } from "lucide-react";
import CardSwap, { Card } from "@/components/CardSwap/CardSwap";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export default function Home() {
    const [isLoginOpen, setIsLoginOpen] = useState(false);
    return (
        <div className="min-h-screen bg-slate-950 text-white relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-gradient-to-br from-brand-950/20 via-slate-950 to-slate-950" />
            <div
                className="absolute inset-0 opacity-5"
                style={{
                    backgroundImage: 'linear-gradient(to right, #14b1e5 1px, transparent 1px), linear-gradient(to bottom, #14b1e5 1px, transparent 1px)',
                    backgroundSize: '60px 60px'
                }}
            />

            {/* Header */}
            <header className="relative z-10 border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl">
                <div className="container mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="hover:opacity-80 transition-opacity">
                            <div className="w-16 h-16 relative flex items-center justify-center">
                                <Image
                                    src="/harvest-logo.png"
                                    alt="Project Harvest Logo"
                                    width={64}
                                    height={64}
                                    className="object-contain rounded-xl"
                                    priority
                                />
                            </div>
                        </Link>
                        <a
                            href="https://abgumich.org/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50 hover:border-brand-500/50 hover:bg-slate-800/80 transition-all"
                        >
                            <div className="w-6 h-6 rounded-full overflow-hidden flex items-center justify-center">
                                <Image
                                    src="/abg-logo.png"
                                    alt="AI Business Group Logo"
                                    width={24}
                                    height={24}
                                    className="object-contain w-full h-full"
                                />
                            </div>
                            <span className="text-sm font-medium text-slate-300">Powered by AI Business Group @ University of Michigan</span>
                        </a>
                    </div>

                    <div className="flex items-center gap-3">
                        <Dialog open={isLoginOpen} onOpenChange={setIsLoginOpen}>
                            <DialogTrigger asChild>
                                <Button variant="outline" className="border-brand-500/30 text-brand-300 hover:bg-brand-500/10 hover:text-brand-200 font-medium">
                                    <LogIn className="w-4 h-4 mr-2" />
                                    Login
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="bg-slate-900 border-slate-800 text-white">
                                <DialogHeader>
                                    <DialogTitle className="text-2xl font-bold">Welcome Back</DialogTitle>
                                    <DialogDescription className="text-slate-400">
                                        Login to access your saved data visualizations and analytics
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 py-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-300">Email</label>
                                        <div className="relative">
                                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            <Input
                                                type="email"
                                                placeholder="you@example.com"
                                                className="pl-10 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-brand-500"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-300">Password</label>
                                        <div className="relative">
                                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            <Input
                                                type="password"
                                                placeholder="••••••••"
                                                className="pl-10 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-brand-500"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <label className="flex items-center gap-2 cursor-pointer text-slate-400">
                                            <input type="checkbox" className="rounded border-slate-700 bg-slate-800/50" />
                                            Remember me
                                        </label>
                                        <button className="text-brand-400 hover:text-brand-300">Forgot password?</button>
                                    </div>
                                    <Button className="w-full bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-lg shadow-brand-500/30 font-medium">
                                        Sign In
                                        <ArrowRight className="w-4 h-4 ml-2" />
                                    </Button>
                                    <div className="text-center text-sm text-slate-400">
                                        Don't have an account? <button className="text-brand-400 hover:text-brand-300 font-medium">Sign up</button>
                                    </div>
                                </div>
                            </DialogContent>
                        </Dialog>

                        <Link href="/analyzer">
                            <Button className="bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-lg shadow-brand-500/30 font-medium">
                                Launch Analyzer
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="relative z-10 container mx-auto px-6 py-20 min-h-[calc(100vh-80px)] flex items-center">
                <div className="grid lg:grid-cols-2 gap-12 items-center w-full">
                    {/* Left Content */}
                    <div className="space-y-8">
                        <h2 className="text-6xl md:text-8xl font-bold leading-tight tracking-tight">
                            <span className="text-white">Project </span>
                            <span className="bg-gradient-to-r from-brand-400 to-brand-600 bg-clip-text text-transparent">
                                Harvest
                            </span>
                        </h2>

                        <p className="text-lg text-slate-400 leading-relaxed max-w-xl mt-6">
                            Transform your Fortnite map activations with AI-powered analytics.
                            Track performance, analyze social media impact, and generate insights in real-time.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Link href="/analyzer">
                                <Button
                                    size="lg"
                                    className="bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-2xl shadow-brand-500/30 text-lg px-8"
                                >
                                    <Zap className="w-5 h-5 mr-2" />
                                    Start Analyzing
                                    <ArrowRight className="w-5 h-5 ml-2" />
                                </Button>
                            </Link>
                            <Button
                                size="lg"
                                variant="outline"
                                className="border-brand-500/30 text-brand-300 hover:bg-brand-500/10 hover:text-brand-200 text-lg"
                            >
                                <BarChart3 className="w-5 h-5 mr-2" />
                                View Demo
                            </Button>
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-3 gap-6 pt-8 border-t border-slate-800/50">
                            <div>
                                <div className="text-3xl font-bold text-brand-400">24/7</div>
                                <div className="text-sm text-slate-500">Real-time Tracking</div>
                            </div>
                            <div>
                                <div className="text-3xl font-bold text-brand-400">10M+</div>
                                <div className="text-sm text-slate-500">Data Points Analyzed</div>
                            </div>
                            <div>
                                <div className="text-3xl font-bold text-brand-400">AI</div>
                                <div className="text-sm text-slate-500">Powered Insights</div>
                            </div>
                        </div>
                    </div>

                    {/* Right Content - Card Swap */}
                    <div className="relative h-[600px] hidden lg:block">
                        <CardSwap
                            width={400}
                            height={500}
                            cardDistance={50}
                            verticalDistance={60}
                            delay={4000}
                            pauseOnHover={true}
                            easing="elastic"
                        >
                            <Card>
                                <div className="p-8 h-full flex flex-col justify-between">
                                    <div>
                                        <div className="w-12 h-12 bg-gradient-to-br from-brand-500/20 to-brand-600/20 rounded-xl flex items-center justify-center mb-4 border border-brand-500/30">
                                            <BarChart3 className="w-6 h-6 text-brand-400" />
                                        </div>
                                        <h3 className="text-2xl font-bold mb-3">Map Performance</h3>
                                        <p className="text-slate-400">
                                            Track CCU, retention rates, and player engagement across all your Fortnite map activations.
                                        </p>
                                    </div>
                                    <div className="space-y-2 mt-6">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-slate-400">Peak CCU</span>
                                            <span className="text-brand-400 font-semibold">2.3M</span>
                                        </div>
                                        <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                                            <div className="h-full bg-gradient-to-r from-brand-500 to-brand-400" style={{ width: '75%' }} />
                                        </div>
                                    </div>
                                </div>
                            </Card>
                            <Card>
                                <div className="p-8 h-full flex flex-col justify-between">
                                    <div>
                                        <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-xl flex items-center justify-center mb-4 border border-purple-500/30">
                                            <Sparkles className="w-6 h-6 text-purple-400" />
                                        </div>
                                        <h3 className="text-2xl font-bold mb-3">AI Insights</h3>
                                        <p className="text-slate-400">
                                            Generate custom visualizations, predict future performance trends, and get AI-powered recommendations for your activations.
                                        </p>
                                    </div>
                                    <div className="bg-gradient-to-r from-purple-500/10 to-brand-500/10 border border-purple-500/20 rounded-lg p-4 mt-6">
                                        <p className="text-xs text-purple-300 font-medium">🔮 AI Prediction</p>
                                        <p className="text-sm text-slate-300 mt-2">Your next activation will peak at 2.8M CCU with 85% confidence</p>
                                    </div>
                                </div>
                            </Card>
                            <Card>
                                <div className="p-8 h-full flex flex-col justify-between">
                                    <div>
                                        <div className="w-12 h-12 bg-gradient-to-br from-green-500/20 to-emerald-600/20 rounded-xl flex items-center justify-center mb-4 border border-green-500/30">
                                            <Zap className="w-6 h-6 text-green-400" />
                                        </div>
                                        <h3 className="text-2xl font-bold mb-3">Social Analytics</h3>
                                        <p className="text-slate-400">
                                            Monitor mentions, sentiment, and trends across Twitter, TikTok, YouTube, and Instagram.
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3 mt-6">
                                        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                                            <div className="text-lg font-bold text-brand-400">45K</div>
                                            <div className="text-xs text-slate-500">Mentions</div>
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                                            <div className="text-lg font-bold text-green-400">+340%</div>
                                            <div className="text-xs text-slate-500">Growth</div>
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        </CardSwap>
                    </div>
                </div>
            </div>

            {/* Bottom Section */}
            <div className="relative z-10 border-t border-slate-800/50 bg-slate-900/50 backdrop-blur-xl">
                <div className="container mx-auto px-6 py-12">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div>
                            <p className="text-sm text-slate-400">
                                A collaboration between{' '}
                                <a
                                    href="https://abgumich.org/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-brand-400 font-medium hover:text-brand-300 transition-colors underline decoration-transparent hover:decoration-brand-300"
                                >
                                    University of Michigan AI Business Group
                                </a>
                                ,{' '}
                                <a
                                    href="https://cherrypicktalent.com/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-brand-400 font-medium hover:text-brand-300 transition-colors underline decoration-transparent hover:decoration-brand-300"
                                >
                                    Cherry Pick Talent
                                </a>
                                , and{' '}
                                <a
                                    href="https://www.epicgames.com/site/en-US/home"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-brand-400 font-medium hover:text-brand-300 transition-colors underline decoration-transparent hover:decoration-brand-300"
                                >
                                    Epic Games
                                </a>
                            </p>
                        </div>
                        <div className="flex items-center gap-6">
                            <a
                                href="https://abgumich.org/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-12 h-12 flex items-center justify-center hover:scale-110 transition-transform"
                            >
                                <Image
                                    src="/abg-logo.png"
                                    alt="AI Business Group"
                                    width={48}
                                    height={48}
                                    className="object-contain"
                                />
                            </a>
                            <a
                                href="https://cherrypicktalent.com/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-12 h-12 flex items-center justify-center hover:scale-110 transition-transform"
                            >
                                <Image
                                    src="/cpt-logo.png"
                                    alt="Cherry Pick Talent"
                                    width={48}
                                    height={48}
                                    className="object-contain"
                                />
                            </a>
                            <a
                                href="https://www.epicgames.com/site/en-US/home"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-12 h-12 flex items-center justify-center hover:scale-110 transition-transform"
                            >
                                <Image
                                    src="/eg-logo.svg.png"
                                    alt="Epic Games"
                                    width={48}
                                    height={48}
                                    className="object-contain"
                                />
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
