'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  X,
  Send,
  Zap,
  MapPin,
  FileText,
  Sparkles,
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  suggestions?: string[];
}

export function Copilot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your TerraJinki AI assistant. I can help you find sites, analyze parcels, and answer questions about renewable energy development. What would you like to do?",
      suggestions: [
        'Find 50+ acre parcels in Texas',
        'What makes a good solar site?',
        'Show my project pipeline',
      ],
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getAIResponse(input),
        suggestions: getSuggestions(input),
      };
      setMessages((prev) => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1000);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-lg transition-all ${
          isOpen
            ? 'bg-gray-200 dark:bg-gray-700'
            : 'bg-gradient-to-r from-terra-600 to-jinki-600 hover:from-terra-700 hover:to-jinki-700'
        }`}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-gray-600 dark:text-gray-300" />
        ) : (
          <Sparkles className="w-6 h-6 text-white" />
        )}
      </button>

      {/* Chat panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 z-50 w-96 h-[500px] bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-terra-600 to-jinki-600">
              <div className="p-2 bg-white/20 rounded-lg">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">TerraJinki Copilot</h3>
                <p className="text-xs text-white/80">Powered by Claude</p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div key={message.id}>
                  <div
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-terra-600 text-white rounded-br-md'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-md'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                    </div>
                  </div>

                  {/* Suggestions */}
                  {message.suggestions && message.role === 'assistant' && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {message.suggestions.map((suggestion, i) => (
                        <button
                          key={i}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="px-3 py-1.5 text-xs font-medium text-terra-600 bg-terra-50 dark:bg-terra-900/20 dark:text-terra-400 rounded-full hover:bg-terra-100 dark:hover:bg-terra-900/30 transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask me anything..."
                  className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-full text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-terra-500"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="p-2 bg-terra-600 text-white rounded-full hover:bg-terra-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Simulated AI responses
function getAIResponse(input: string): string {
  const lower = input.toLowerCase();

  if (lower.includes('texas') || lower.includes('tx')) {
    return "I found 847 parcels in Texas matching your criteria. The highest-scoring site is in Harris County (87/100) with 52 acres, excellent grid access, and by-right solar permitting. Would you like me to show these on the map?";
  }

  if (lower.includes('solar site') || lower.includes('good site')) {
    return "A good utility-scale solar site typically has: 1) 50+ acres of relatively flat land (<5% slope), 2) Agricultural zoning with by-right or conditional solar permitting, 3) Within 5 miles of a substation with available capacity, 4) No wetlands, flood zones, or endangered species habitat. Would you like me to search for sites matching these criteria?";
  }

  if (lower.includes('pipeline') || lower.includes('project')) {
    return "You currently have 3 projects in your pipeline: 1) Harris County Solar (85 acres) - Permitting stage, 2) Brazos Wind Farm (120 acres) - Due diligence, 3) Travis Solar+Storage (200 acres) - Prospecting. Would you like details on any of these?";
  }

  if (lower.includes('analyze')) {
    return "I can run a comprehensive site analysis that includes: permitting risk assessment, grid interconnection analysis, environmental screening, and financial modeling. Which parcel would you like me to analyze?";
  }

  return "I understand you're asking about renewable energy site development. Could you please provide more details about what you're looking for? I can help with site search, analysis, permitting questions, and more.";
}

function getSuggestions(input: string): string[] {
  const lower = input.toLowerCase();

  if (lower.includes('texas')) {
    return ['Show on map', 'Filter by score > 80', 'Export list'];
  }

  if (lower.includes('solar site') || lower.includes('good site')) {
    return ['Search in Texas', 'Search in California', 'Set custom filters'];
  }

  if (lower.includes('pipeline')) {
    return ['View Harris project', 'Add new project', 'Export report'];
  }

  return ['Find sites', 'Analyze a parcel', 'View projects'];
}
