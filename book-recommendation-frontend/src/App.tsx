"use client";

import type React from "react";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BookOpen, Send, Bot, User } from "lucide-react";

interface Message {
    id: string;
    content: string;
    isUser: boolean;
    timestamp: Date;
}

export default function BookRecommendationAssistant() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "1",
            content:
                "Hello! I'm your personal book recommendation assistant. Tell me about your reading preferences, favorite genres, or what kind of mood you're in for your next read!",
            isUser: false,
            timestamp: new Date(),
        },
    ]);
    const [inputMessage, setInputMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSendMessage = async () => {
        if (!inputMessage.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            content: inputMessage,
            isUser: true,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputMessage("");
        setIsLoading(true);

        try {
            const response = await fetch("http://localhost:5000/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    query: inputMessage,
                    history: messages.slice(1).map((msg) => {
                        return {
                            role: msg.isUser ? "user" : "assistant",
                            content: msg.content,
                        };
                    }),
                }),
            });

            const data = await response.json();

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                content:
                    data.error !== null
                        ? `Sorry, there was an error: ${data.error}`
                        : data.payload,
                isUser: false,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error("Error sending message:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                content:
                    "I'm having trouble connecting right now. Please try again in a moment!",
                isUser: false,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <header className="bg-emerald-600 text-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center space-x-2">
                            <BookOpen className="h-8 w-8" />
                            <span className="text-xl font-bold">BookWise</span>
                        </div>
                        <nav className="hidden md:flex space-x-8">
                            <a
                                href="#"
                                className="hover:text-white/80 transition-colors"
                            >
                                Home
                            </a>
                            <a
                                href="#"
                                className="hover:text-white/80 transition-colors"
                            >
                                About
                            </a>
                            <a
                                href="#"
                                className="hover:text-white/80 transition-colors"
                            >
                                Recommendations
                            </a>
                            <a
                                href="#"
                                className="hover:text-white/80 transition-colors"
                            >
                                Chat
                            </a>
                        </nav>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Hero Section */}
                <div className="text-center space-y-6 mb-12">
                    <h1 className="text-4xl lg:text-5xl font-bold text-slate-900 leading-tight">
                        Discover Your Next
                        <span className="text-emerald-600 block">
                            Favorite Book
                        </span>
                    </h1>
                    <p className="text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
                        Get personalized book recommendations powered by AI.
                        Whether you're looking for your next thriller, romance,
                        or literary masterpiece, our assistant understands your
                        taste and finds the perfect match.
                    </p>
                </div>

                {/* Chat Interface */}
                <div className="max-w-3xl mx-auto">
                    <Card className="bg-white shadow-lg border-slate-200">
                        <CardContent className="p-0">
                            <div className="border-b border-slate-200 p-4 bg-slate-50">
                                <h3 className="font-semibold text-slate-900">
                                    Chat with BookWise Assistant
                                </h3>
                                <p className="text-sm text-slate-600">
                                    Get personalized book recommendations
                                </p>
                            </div>

                            {/* Messages */}
                            <ScrollArea className="h-96 p-4">
                                <div className="space-y-4">
                                    {messages.map((message) => (
                                        <div
                                            key={message.id}
                                            className={`flex items-start space-x-3 ${
                                                message.isUser
                                                    ? "flex-row-reverse space-x-reverse"
                                                    : ""
                                            }`}
                                        >
                                            <div
                                                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                                                    message.isUser
                                                        ? "bg-blue-500"
                                                        : "bg-emerald-500"
                                                }`}
                                            >
                                                {message.isUser ? (
                                                    <User className="h-4 w-4 text-white" />
                                                ) : (
                                                    <Bot className="h-4 w-4 text-white" />
                                                )}
                                            </div>
                                            <div
                                                className={`max-w-[70%] rounded-lg px-4 py-2 text-sm ${
                                                    message.isUser
                                                        ? "bg-blue-500 text-white"
                                                        : "bg-slate-100 text-slate-800"
                                                }`}
                                            >
                                                {message.content}
                                            </div>
                                        </div>
                                    ))}
                                    {isLoading && (
                                        <div className="flex items-start space-x-3">
                                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center">
                                                <Bot className="h-4 w-4 text-white" />
                                            </div>
                                            <div className="bg-slate-100 text-slate-800 rounded-lg px-4 py-2 text-sm">
                                                <div className="flex space-x-1">
                                                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                                                    <div
                                                        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                                                        style={{
                                                            animationDelay:
                                                                "0.1s",
                                                        }}
                                                    ></div>
                                                    <div
                                                        className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                                                        style={{
                                                            animationDelay:
                                                                "0.2s",
                                                        }}
                                                    ></div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>

                            {/* Input */}
                            <div className="border-t border-slate-200 p-4 bg-slate-50">
                                <div className="flex space-x-2">
                                    <Input
                                        value={inputMessage}
                                        onChange={(e) =>
                                            setInputMessage(e.target.value)
                                        }
                                        onKeyPress={handleKeyPress}
                                        placeholder="Ask for book recommendations..."
                                        className="flex-1 border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                        disabled={isLoading}
                                    />
                                    <Button
                                        onClick={handleSendMessage}
                                        disabled={
                                            !inputMessage.trim() || isLoading
                                        }
                                        size="icon"
                                        className="bg-emerald-600 hover:bg-emerald-700"
                                    >
                                        <Send className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </main>

            {/* Footer */}
            <footer className="bg-slate-800 mt-20">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="text-center space-y-4">
                        <div className="flex items-center justify-center space-x-2">
                            <BookOpen className="h-6 w-6 text-emerald-400" />
                            <span className="text-lg font-bold text-white">
                                BookWise
                            </span>
                        </div>
                        <div className="flex justify-center space-x-6 text-sm text-slate-400">
                            <a
                                href="#"
                                className="hover:text-white transition-colors"
                            >
                                Privacy Policy
                            </a>
                            <a
                                href="#"
                                className="hover:text-white transition-colors"
                            >
                                Terms of Service
                            </a>
                            <a
                                href="#"
                                className="hover:text-white transition-colors"
                            >
                                Contact
                            </a>
                        </div>
                        <p className="text-sm text-slate-400">
                            © 2024 BookWise. Helping readers discover their next
                            favorite book.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
}
